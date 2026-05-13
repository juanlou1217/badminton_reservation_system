from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from sqlalchemy.exc import SQLAlchemyError

from app.db import SessionLocal, init_db
from app.services.auth_service import AuthService, AuthenticationError
from app.ui.admin_window import AdminWindow
from app.ui.user_window import UserWindow


class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("体育馆羽毛球预约系统 - 登录")
        self.geometry("420x300")
        self.resizable(False, False)
        self.session = SessionLocal()
        self._build()

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=24)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="体育馆羽毛球预约系统", font=("Arial", 18, "bold")).pack(pady=(0, 20))

        form = ttk.Frame(frame)
        form.pack(fill=tk.X)
        ttk.Label(form, text="用户名").grid(row=0, column=0, sticky=tk.W, pady=6)
        ttk.Label(form, text="密码").grid(row=1, column=0, sticky=tk.W, pady=6)
        ttk.Label(form, text="手机号").grid(row=2, column=0, sticky=tk.W, pady=6)

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.username_var).grid(row=0, column=1, sticky=tk.EW, padx=(12, 0))
        ttk.Entry(form, textvariable=self.password_var, show="*").grid(row=1, column=1, sticky=tk.EW, padx=(12, 0))
        ttk.Entry(form, textvariable=self.phone_var).grid(row=2, column=1, sticky=tk.EW, padx=(12, 0))
        form.columnconfigure(1, weight=1)

        actions = ttk.Frame(frame)
        actions.pack(fill=tk.X, pady=(20, 0))
        ttk.Button(actions, text="登录", command=self.login).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(actions, text="注册普通用户", command=self.register).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(12, 0))

    def login(self) -> None:
        service = AuthService(self.session)
        try:
            user = service.authenticate(self.username_var.get(), self.password_var.get())
        except AuthenticationError as exc:
            messagebox.showerror("登录失败", str(exc))
            return
        if user.role == "admin":
            AdminWindow(self, self.session, user)
        else:
            UserWindow(self, self.session, user)
        self.withdraw()

    def register(self) -> None:
        service = AuthService(self.session)
        try:
            service.register_user(
                self.username_var.get(),
                self.phone_var.get(),
                self.password_var.get(),
            )
        except AuthenticationError as exc:
            messagebox.showerror("注册失败", str(exc))
            return
        messagebox.showinfo("注册成功", "普通用户账号已创建，请登录。")

    def destroy(self) -> None:
        self.session.close()
        super().destroy()


def run_app() -> None:
    try:
        init_db()
        app = LoginWindow()
    except (RuntimeError, SQLAlchemyError) as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("启动失败", f"数据库初始化失败：{exc}")
        root.destroy()
        return
    app.mainloop()
