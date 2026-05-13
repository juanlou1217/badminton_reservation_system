from __future__ import annotations

import tkinter as tk
from datetime import time
from tkinter import filedialog, messagebox, ttk

from sqlalchemy.orm import Session
from tkcalendar import DateEntry

from app.models import Court, User
from app.services.admin_service import AdminService
from app.services.court_service import CourtService
from app.services.export_service import ExportService
from app.services.reservation_service import ReservationError, ReservationService
from app.services.settings_service import SettingsService
from app.services.stats_service import StatsService


class AdminWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk, session: Session, current_user: User):
        super().__init__(parent)
        self.parent = parent
        self.session = session
        self.current_user = current_user
        self.courts: list[Court] = []
        self.title(f"管理员 - {current_user.username}")
        self.geometry("980x620")
        self.protocol("WM_DELETE_WINDOW", self.logout)
        self._build()
        self.refresh_all()

    def _build(self) -> None:
        top = ttk.Frame(self, padding=(12, 8))
        top.pack(fill=tk.X)
        ttk.Label(top, text=f"管理员：{self.current_user.username}").pack(side=tk.LEFT)
        ttk.Button(top, text="退出登录", command=self.logout).pack(side=tk.RIGHT)

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        notebook.add(self._build_users_tab(notebook), text="用户管理")
        notebook.add(self._build_courts_tab(notebook), text="场地管理")
        notebook.add(self._build_slots_tab(notebook), text="时间段管理")
        notebook.add(self._build_reservations_tab(notebook), text="预约管理")
        notebook.add(self._build_settings_tab(notebook), text="系统设置")
        notebook.add(self._build_export_tab(notebook), text="统计导出")

    def _build_users_tab(self, parent) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=8)
        self.user_tree = ttk.Treeview(frame, columns=("username", "phone", "role", "status"), show="headings")
        for key, text in (("username", "用户名"), ("phone", "手机号"), ("role", "角色"), ("status", "状态")):
            self.user_tree.heading(key, text=text)
        self.user_tree.pack(fill=tk.BOTH, expand=True)
        actions = ttk.Frame(frame)
        actions.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(actions, text="启用", command=lambda: self.set_selected_user_status("normal")).pack(side=tk.RIGHT)
        ttk.Button(actions, text="禁用", command=lambda: self.set_selected_user_status("disabled")).pack(side=tk.RIGHT, padx=(0, 8))
        ttk.Button(actions, text="刷新", command=self.refresh_users).pack(side=tk.RIGHT, padx=(0, 8))
        return frame

    def _build_courts_tab(self, parent) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=8)
        form = ttk.Frame(frame)
        form.pack(fill=tk.X)
        self.court_no_var = tk.StringVar()
        self.court_name_var = tk.StringVar()
        self.court_location_var = tk.StringVar()
        for idx, (label, variable) in enumerate(
            (("编号", self.court_no_var), ("名称", self.court_name_var), ("位置", self.court_location_var))
        ):
            ttk.Label(form, text=label).grid(row=0, column=idx * 2, padx=(0, 6))
            ttk.Entry(form, textvariable=variable, width=18).grid(row=0, column=idx * 2 + 1, padx=(0, 12))
        ttk.Button(form, text="新增场地", command=self.create_court).grid(row=0, column=6)

        self.admin_court_tree = ttk.Treeview(frame, columns=("no", "name", "location", "status"), show="headings")
        for key, text in (("no", "编号"), ("name", "名称"), ("location", "位置"), ("status", "状态")):
            self.admin_court_tree.heading(key, text=text)
        self.admin_court_tree.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        actions = ttk.Frame(frame)
        actions.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(actions, text="开放", command=lambda: self.set_selected_court_status("open")).pack(side=tk.RIGHT)
        ttk.Button(actions, text="停用", command=lambda: self.set_selected_court_status("closed")).pack(
            side=tk.RIGHT,
            padx=(0, 8),
        )
        return frame

    def _build_slots_tab(self, parent) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=8)
        controls = ttk.Frame(frame)
        controls.pack(fill=tk.X)
        ttk.Label(controls, text="场地").pack(side=tk.LEFT)
        self.admin_court_combo = ttk.Combobox(controls, state="readonly", width=28)
        self.admin_court_combo.pack(side=tk.LEFT, padx=(8, 16))
        ttk.Label(controls, text="开始日期").pack(side=tk.LEFT)
        self.slot_start_date = DateEntry(controls, date_pattern="yyyy-mm-dd")
        self.slot_start_date.pack(side=tk.LEFT, padx=(8, 16))
        ttk.Label(controls, text="结束日期").pack(side=tk.LEFT)
        self.slot_end_date = DateEntry(controls, date_pattern="yyyy-mm-dd")
        self.slot_end_date.pack(side=tk.LEFT, padx=(8, 16))
        ttk.Button(controls, text="生成默认时间段", command=self.generate_slots).pack(side=tk.LEFT)
        ttk.Button(controls, text="刷新列表", command=self.refresh_slots).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Label(frame, text="默认生成：08:00-10:00、10:00-12:00、14:00-16:00、16:00-18:00").pack(
            anchor=tk.W,
            pady=(12, 0),
        )
        self.admin_slot_tree = ttk.Treeview(
            frame,
            columns=("court", "date", "time", "status"),
            show="headings",
        )
        for key, text in (("court", "场地"), ("date", "日期"), ("time", "时间"), ("status", "状态")):
            self.admin_slot_tree.heading(key, text=text)
        self.admin_slot_tree.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        actions = ttk.Frame(frame)
        actions.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(actions, text="设为可预约", command=lambda: self.set_selected_slot_status("available")).pack(
            side=tk.RIGHT,
        )
        ttk.Button(actions, text="暂停开放", command=lambda: self.set_selected_slot_status("disabled")).pack(
            side=tk.RIGHT,
            padx=(0, 8),
        )
        return frame

    def _build_reservations_tab(self, parent) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=8)
        filters = ttk.Frame(frame)
        filters.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(filters, text="用户").pack(side=tk.LEFT)
        self.reservation_user_filter = tk.StringVar()
        ttk.Entry(filters, textvariable=self.reservation_user_filter, width=14).pack(side=tk.LEFT, padx=(6, 12))
        ttk.Label(filters, text="状态").pack(side=tk.LEFT)
        self.reservation_status_filter = tk.StringVar(value="全部")
        ttk.Combobox(
            filters,
            textvariable=self.reservation_status_filter,
            values=("全部", "booked", "cancelled", "finished"),
            state="readonly",
            width=12,
        ).pack(side=tk.LEFT, padx=(6, 12))
        self.reservation_date_filter_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(filters, text="日期", variable=self.reservation_date_filter_enabled).pack(side=tk.LEFT)
        self.reservation_date_filter = DateEntry(filters, date_pattern="yyyy-mm-dd", width=12)
        self.reservation_date_filter.pack(side=tk.LEFT, padx=(6, 12))
        ttk.Button(filters, text="筛选", command=self.refresh_reservations).pack(side=tk.LEFT)
        ttk.Button(filters, text="重置", command=self.reset_reservation_filters).pack(side=tk.LEFT, padx=(8, 0))
        self.admin_reservation_tree = ttk.Treeview(
            frame,
            columns=("no", "user", "court", "date", "time", "status"),
            show="headings",
        )
        for key, text in (
            ("no", "预约编号"),
            ("user", "用户"),
            ("court", "场地"),
            ("date", "日期"),
            ("time", "时间"),
            ("status", "状态"),
        ):
            self.admin_reservation_tree.heading(key, text=text)
        self.admin_reservation_tree.pack(fill=tk.BOTH, expand=True)
        actions = ttk.Frame(frame)
        actions.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(actions, text="取消选中预约", command=self.cancel_selected_reservation).pack(side=tk.RIGHT)
        ttk.Button(actions, text="刷新", command=self.refresh_reservations).pack(side=tk.RIGHT, padx=(0, 8))
        return frame

    def _build_export_tab(self, parent) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=24)
        self.stats_text = tk.StringVar(value="点击刷新统计查看当前预约数据")
        ttk.Label(frame, textvariable=self.stats_text, justify=tk.LEFT).pack(anchor=tk.W, fill=tk.X)
        ttk.Button(frame, text="刷新统计", command=self.refresh_stats).pack(anchor=tk.W, pady=(12, 0))
        ttk.Label(frame, text="导出全部预约记录为 Excel 文件").pack(anchor=tk.W)
        ttk.Button(frame, text="选择路径并导出", command=self.export_reservations).pack(anchor=tk.W, pady=(16, 0))
        return frame

    def _build_settings_tab(self, parent) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=24)
        ttk.Label(frame, text="单个用户每天最多预约次数").grid(row=0, column=0, sticky=tk.W, pady=8)
        self.max_daily_var = tk.StringVar(value="2")
        ttk.Entry(frame, textvariable=self.max_daily_var, width=12).grid(row=0, column=1, sticky=tk.W, pady=8, padx=(12, 0))
        ttk.Label(frame, text="系统公告").grid(row=1, column=0, sticky=tk.NW, pady=8)
        self.announcement_text = tk.Text(frame, width=60, height=6)
        self.announcement_text.grid(row=1, column=1, sticky=tk.W, pady=8, padx=(12, 0))
        ttk.Button(frame, text="保存设置", command=self.save_settings).grid(row=2, column=1, sticky=tk.E, pady=(12, 0))
        return frame

    def refresh_all(self) -> None:
        self.refresh_users()
        self.refresh_courts()
        self.refresh_slots()
        self.refresh_reservations()
        self.refresh_settings()
        self.refresh_stats()

    def refresh_users(self) -> None:
        self.user_tree.delete(*self.user_tree.get_children())
        for user in AdminService(self.session, self.current_user).list_users():
            self.user_tree.insert(
                "",
                tk.END,
                iid=str(user.id),
                values=(user.username, user.phone, user.role, user.status),
            )

    def refresh_courts(self) -> None:
        self.courts = CourtService(self.session).search_courts()
        self.admin_court_tree.delete(*self.admin_court_tree.get_children())
        self.admin_court_combo["values"] = [f"{court.court_no} - {court.name}" for court in self.courts]
        for court in self.courts:
            self.admin_court_tree.insert(
                "",
                tk.END,
                iid=str(court.id),
                values=(court.court_no, court.name, court.location, court.status),
            )

    def refresh_reservations(self) -> None:
        status = self.reservation_status_filter.get()
        if status == "全部":
            status = ""
        reservations = ReservationService(self.session).list_all_reservations(
            current_user=self.current_user,
            username=self.reservation_user_filter.get(),
            status=status,
            slot_date=self.reservation_date_filter.get_date() if self.reservation_date_filter_enabled.get() else None,
        )
        self.admin_reservation_tree.delete(*self.admin_reservation_tree.get_children())
        for item in reservations:
            time_text = f"{item.slot.start_time}-{item.slot.end_time}" if item.slot else ""
            self.admin_reservation_tree.insert(
                "",
                tk.END,
                iid=str(item.id),
                values=(
                    item.reservation_no,
                    item.user.username if item.user else "",
                    item.court.name if item.court else "",
                    item.slot.slot_date if item.slot else "",
                    time_text,
                    item.status,
                ),
            )

    def refresh_slots(self) -> None:
        self.admin_slot_tree.delete(*self.admin_slot_tree.get_children())
        for slot in AdminService(self.session, self.current_user).list_slots():
            court_text = f"{slot.court.court_no} - {slot.court.name}" if slot.court else str(slot.court_id)
            time_text = f"{slot.start_time}-{slot.end_time}"
            self.admin_slot_tree.insert(
                "",
                tk.END,
                iid=str(slot.id),
                values=(court_text, slot.slot_date, time_text, slot.status),
            )

    def reset_reservation_filters(self) -> None:
        self.reservation_user_filter.set("")
        self.reservation_status_filter.set("全部")
        self.reservation_date_filter_enabled.set(False)
        self.refresh_reservations()

    def create_court(self) -> None:
        try:
            AdminService(self.session, self.current_user).create_court(
                self.court_no_var.get(),
                self.court_name_var.get(),
                self.court_location_var.get(),
            )
        except ValueError as exc:
            messagebox.showerror("新增失败", str(exc))
            return
        self.refresh_courts()

    def set_selected_user_status(self, status: str) -> None:
        item = self._selected_iid(self.user_tree)
        if item is None:
            return
        AdminService(self.session, self.current_user).set_user_status(int(item), status)
        self.refresh_users()

    def set_selected_court_status(self, status: str) -> None:
        item = self._selected_iid(self.admin_court_tree)
        if item is None:
            return
        AdminService(self.session, self.current_user).update_court_status(int(item), status)
        self.refresh_courts()

    def generate_slots(self) -> None:
        selected = self.admin_court_combo.current()
        if selected < 0:
            messagebox.showwarning("提示", "请先选择场地")
            return
        ranges = [
            (time(8, 0), time(10, 0)),
            (time(10, 0), time(12, 0)),
            (time(14, 0), time(16, 0)),
            (time(16, 0), time(18, 0)),
        ]
        slots = AdminService(self.session, self.current_user).generate_slots(
            self.courts[selected].id,
            self.slot_start_date.get_date(),
            self.slot_end_date.get_date(),
            ranges,
        )
        messagebox.showinfo("生成完成", f"新增 {len(slots)} 个时间段。")
        self.refresh_slots()

    def set_selected_slot_status(self, status: str) -> None:
        item = self._selected_iid(self.admin_slot_tree)
        if item is None:
            return
        try:
            AdminService(self.session, self.current_user).set_slot_status(int(item), status)
        except ValueError as exc:
            messagebox.showerror("修改失败", str(exc))
            return
        self.refresh_slots()

    def cancel_selected_reservation(self) -> None:
        item = self._selected_iid(self.admin_reservation_tree)
        if item is None:
            return
        try:
            ReservationService(self.session).cancel_reservation(int(item), self.current_user)
        except ReservationError as exc:
            messagebox.showerror("取消失败", str(exc))
            return
        self.refresh_reservations()

    def export_reservations(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel 文件", "*.xlsx")],
            initialfile="预约记录.xlsx",
        )
        if not path:
            return
        ExportService(self.session, self.current_user).export_reservations_to_xlsx(path)
        messagebox.showinfo("导出成功", f"已导出到：{path}")

    def refresh_settings(self) -> None:
        service = SettingsService(self.session)
        self.max_daily_var.set(str(service.get_int("max_daily_reservations", 2)))
        self.announcement_text.delete("1.0", tk.END)
        self.announcement_text.insert("1.0", service.get_value("announcement", ""))

    def save_settings(self) -> None:
        try:
            max_daily = int(self.max_daily_var.get())
        except ValueError:
            messagebox.showerror("保存失败", "每日预约次数必须是数字")
            return
        if max_daily < 1:
            messagebox.showerror("保存失败", "每日预约次数必须大于 0")
            return
        service = SettingsService(self.session, self.current_user)
        service.set_value("max_daily_reservations", str(max_daily), "单个用户每天最多预约次数")
        service.set_value("announcement", self.announcement_text.get("1.0", tk.END).strip(), "系统公告")
        messagebox.showinfo("保存成功", "系统设置已保存。")

    def refresh_stats(self) -> None:
        summary = StatsService(self.session, self.current_user).reservation_summary()
        court_lines = ", ".join(f"{item['court']} {item['count']} 次" for item in summary["by_court"]) or "暂无"
        date_lines = ", ".join(f"{item['date']} {item['count']} 次" for item in summary["by_date"]) or "暂无"
        self.stats_text.set(
            f"预约总数：{summary['total']}\\n"
            f"有效预约：{summary['booked']}\\n"
            f"已取消：{summary['cancelled']}\\n"
            f"场地使用统计：{court_lines}\\n"
            f"每日预约统计：{date_lines}"
        )

    def _selected_iid(self, tree: ttk.Treeview) -> str | None:
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一条记录")
            return None
        return selection[0]

    def logout(self) -> None:
        self.destroy()
        self.parent.deiconify()
