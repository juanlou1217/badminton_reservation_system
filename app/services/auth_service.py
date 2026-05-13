from __future__ import annotations

from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import User


class AuthenticationError(Exception):
    """Raised when login or registration cannot be completed."""


class AuthService:
    def __init__(self, session: Session):
        self.session = session

    def register_user(self, username: str, phone: str, password: str) -> User:
        return self._register(username, phone, password, role="user")

    def register_admin(self, username: str, phone: str, password: str) -> User:
        return self._register(username, phone, password, role="admin")

    def authenticate(self, username: str, password: str) -> User:
        user = self.session.query(User).filter_by(username=username.strip()).one_or_none()
        if user is None or not check_password_hash(user.password_hash, password):
            raise AuthenticationError("账号或密码错误")
        if user.status == "disabled":
            raise AuthenticationError("账号已被禁用")
        return user

    def _register(self, username: str, phone: str, password: str, role: str) -> User:
        username = username.strip()
        phone = phone.strip()
        if not username or not password:
            raise AuthenticationError("用户名和密码不能为空")
        exists = self.session.query(User).filter_by(username=username).one_or_none()
        if exists is not None:
            raise AuthenticationError("用户名已存在")
        user = User(
            username=username,
            phone=phone,
            password_hash=generate_password_hash(password, method="pbkdf2:sha256"),
            role=role,
            status="normal",
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
