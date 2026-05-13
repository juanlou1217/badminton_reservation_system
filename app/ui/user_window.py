from __future__ import annotations

import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from sqlalchemy.orm import Session
from tkcalendar import DateEntry

from app.display_labels import (
    RESERVATION_STATUS_FILTER_LABELS,
    court_status_label,
    reservation_status_label,
    reservation_status_value,
    slot_status_label,
)
from app.models import Court, TimeSlot, User
from app.services.court_service import CourtService
from app.services.reservation_service import ReservationError, ReservationService
from app.services.settings_service import SettingsService
from app.services.slot_service import SlotService
from app.ui.treeview_helpers import configure_tree_columns


class UserWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk, session: Session, current_user: User):
        super().__init__(parent)
        self.parent = parent
        self.session = session
        self.current_user = current_user
        self.courts: list[Court] = []
        self.slots: list[TimeSlot] = []
        self.title(f"普通用户 - {current_user.username}")
        self.geometry("900x560")
        self.protocol("WM_DELETE_WINDOW", self.logout)
        self._build()
        self.refresh_all()

    def _build(self) -> None:
        top = ttk.Frame(self, padding=(12, 8))
        top.pack(fill=tk.X)
        ttk.Label(top, text=f"当前用户：{self.current_user.username}").pack(side=tk.LEFT)
        self.announcement_var = tk.StringVar(value="")
        ttk.Label(top, textvariable=self.announcement_var).pack(side=tk.LEFT, padx=(24, 0))
        ttk.Button(top, text="退出登录", command=self.logout).pack(side=tk.RIGHT)

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        notebook.add(self._build_court_tab(notebook), text="场地查询")
        notebook.add(self._build_booking_tab(notebook), text="我要预约")
        notebook.add(self._build_reservation_tab(notebook), text="我的预约")

    def _build_court_tab(self, parent) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=8)
        filters = ttk.Frame(frame)
        filters.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(filters, text="场地").pack(side=tk.LEFT)
        self.court_keyword_var = tk.StringVar()
        ttk.Entry(filters, textvariable=self.court_keyword_var, width=20).pack(side=tk.LEFT, padx=(6, 12))
        ttk.Button(filters, text="搜索", command=self.refresh_courts).pack(side=tk.LEFT)
        ttk.Button(filters, text="重置", command=self.reset_court_filter).pack(side=tk.LEFT, padx=(8, 0))
        self.court_tree = ttk.Treeview(frame, columns=("no", "name", "location", "status"), show="headings")
        configure_tree_columns(
            self.court_tree,
            (("no", "编号"), ("name", "名称"), ("location", "位置"), ("status", "状态")),
        )
        self.court_tree.pack(fill=tk.BOTH, expand=True)
        return frame

    def _build_booking_tab(self, parent) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=8)
        controls = ttk.Frame(frame)
        controls.pack(fill=tk.X)
        ttk.Label(controls, text="日期").pack(side=tk.LEFT)
        self.booking_date = DateEntry(controls, date_pattern="yyyy-mm-dd")
        self.booking_date.pack(side=tk.LEFT, padx=(8, 16))
        ttk.Label(controls, text="场地").pack(side=tk.LEFT)
        self.court_combo = ttk.Combobox(controls, state="readonly", width=24)
        self.court_combo.pack(side=tk.LEFT, padx=(8, 16))
        ttk.Button(controls, text="查询时间段", command=self.refresh_slots).pack(side=tk.LEFT)
        ttk.Button(controls, text="预约选中时间段", command=self.book_selected_slot).pack(side=tk.RIGHT)

        self.slot_tree = ttk.Treeview(frame, columns=("date", "start", "end", "status"), show="headings")
        configure_tree_columns(
            self.slot_tree,
            (("date", "日期"), ("start", "开始"), ("end", "结束"), ("status", "状态")),
        )
        self.slot_tree.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        return frame

    def _build_reservation_tab(self, parent) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=8)
        filters = ttk.Frame(frame)
        filters.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(filters, text="状态").pack(side=tk.LEFT)
        self.user_reservation_status_filter = tk.StringVar(value="全部")
        ttk.Combobox(
            filters,
            textvariable=self.user_reservation_status_filter,
            values=RESERVATION_STATUS_FILTER_LABELS,
            state="readonly",
            width=12,
        ).pack(side=tk.LEFT, padx=(6, 12))
        self.user_reservation_date_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(filters, text="日期", variable=self.user_reservation_date_enabled).pack(side=tk.LEFT)
        self.user_reservation_date_filter = DateEntry(filters, date_pattern="yyyy-mm-dd", width=12)
        self.user_reservation_date_filter.pack(side=tk.LEFT, padx=(6, 12))
        ttk.Button(filters, text="筛选", command=self.refresh_reservations).pack(side=tk.LEFT)
        ttk.Button(filters, text="重置", command=self.reset_reservation_filters).pack(side=tk.LEFT, padx=(8, 0))
        self.reservation_tree = ttk.Treeview(
            frame,
            columns=("no", "court", "date", "time", "status"),
            show="headings",
        )
        configure_tree_columns(
            self.reservation_tree,
            (("no", "预约编号"), ("court", "场地"), ("date", "日期"), ("time", "时间"), ("status", "状态")),
        )
        self.reservation_tree.pack(fill=tk.BOTH, expand=True)
        actions = ttk.Frame(frame)
        actions.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(actions, text="刷新", command=self.refresh_reservations).pack(side=tk.RIGHT)
        ttk.Button(actions, text="取消选中预约", command=self.cancel_selected_reservation).pack(side=tk.RIGHT, padx=(0, 8))
        return frame

    def refresh_all(self) -> None:
        self.refresh_announcement()
        self.refresh_courts()
        self.refresh_reservations()

    def refresh_announcement(self) -> None:
        announcement = SettingsService(self.session).get_value("announcement", "")
        self.announcement_var.set(f"公告：{announcement}" if announcement else "")

    def refresh_courts(self) -> None:
        self.courts = CourtService(self.session).list_open_courts(self.court_keyword_var.get())
        self.court_tree.delete(*self.court_tree.get_children())
        self.court_combo["values"] = [f"{court.court_no} - {court.name}" for court in self.courts]
        for court in self.courts:
            self.court_tree.insert(
                "",
                tk.END,
                iid=str(court.id),
                values=(court.court_no, court.name, court.location, court_status_label(court.status)),
            )

    def reset_court_filter(self) -> None:
        self.court_keyword_var.set("")
        self.refresh_courts()

    def refresh_slots(self) -> None:
        selected = self.court_combo.current()
        if selected < 0:
            messagebox.showwarning("提示", "请先选择场地")
            return
        court = self.courts[selected]
        selected_date: date = self.booking_date.get_date()
        self.slots = SlotService(self.session).list_available_slots(court.id, selected_date)
        self.slot_tree.delete(*self.slot_tree.get_children())
        for slot in self.slots:
            self.slot_tree.insert(
                "",
                tk.END,
                iid=str(slot.id),
                values=(slot.slot_date, slot.start_time, slot.end_time, slot_status_label(slot.status)),
            )

    def book_selected_slot(self) -> None:
        item = self._selected_iid(self.slot_tree)
        if item is None:
            return
        try:
            ReservationService(self.session).create_reservation(self.current_user.id, int(item))
        except ReservationError as exc:
            messagebox.showerror("预约失败", str(exc))
            return
        messagebox.showinfo("预约成功", "预约已提交。")
        self.refresh_slots()
        self.refresh_reservations()

    def refresh_reservations(self) -> None:
        status = reservation_status_value(self.user_reservation_status_filter.get())
        reservations = ReservationService(self.session).list_user_reservations(
            self.current_user.id,
            status=status,
            slot_date=self.user_reservation_date_filter.get_date()
            if self.user_reservation_date_enabled.get()
            else None,
        )
        self.reservation_tree.delete(*self.reservation_tree.get_children())
        for item in reservations:
            time_text = f"{item.slot.start_time}-{item.slot.end_time}" if item.slot else ""
            self.reservation_tree.insert(
                "",
                tk.END,
                iid=str(item.id),
                values=(
                    item.reservation_no,
                    item.court.name if item.court else "",
                    item.slot.slot_date if item.slot else "",
                    time_text,
                    reservation_status_label(item.status),
                ),
            )

    def reset_reservation_filters(self) -> None:
        self.user_reservation_status_filter.set("全部")
        self.user_reservation_date_enabled.set(False)
        self.refresh_reservations()

    def cancel_selected_reservation(self) -> None:
        item = self._selected_iid(self.reservation_tree)
        if item is None:
            return
        try:
            ReservationService(self.session).cancel_reservation(int(item), self.current_user)
        except ReservationError as exc:
            messagebox.showerror("取消失败", str(exc))
            return
        self.refresh_reservations()

    def _selected_iid(self, tree: ttk.Treeview) -> str | None:
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一条记录")
            return None
        return selection[0]

    def logout(self) -> None:
        self.destroy()
        self.parent.deiconify()
