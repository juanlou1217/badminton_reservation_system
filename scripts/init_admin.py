from __future__ import annotations

import getpass

from app.db import SessionLocal, init_db
from app.services.auth_service import AuthService, AuthenticationError


def main() -> None:
    init_db()
    username = input("管理员用户名 [admin]: ").strip() or "admin"
    phone = input("管理员手机号 [13800000000]: ").strip() or "13800000000"
    password = getpass.getpass("管理员密码: ")
    if not password:
        raise SystemExit("密码不能为空")
    session = SessionLocal()
    try:
        AuthService(session).register_admin(username, phone, password)
    except AuthenticationError as exc:
        raise SystemExit(str(exc)) from exc
    finally:
        session.close()
    print("管理员账号创建完成")


if __name__ == "__main__":
    main()
