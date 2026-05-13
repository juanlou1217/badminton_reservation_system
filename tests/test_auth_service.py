from __future__ import annotations

import pytest

from app.models import User
from app.services.auth_service import AuthService, AuthenticationError


def test_register_user_hashes_password_and_defaults_to_user_role(db_session):
    service = AuthService(db_session)

    created = service.register_user("bob", "13700000000", "secret123")

    assert created.username == "bob"
    assert created.role == "user"
    assert created.status == "normal"
    assert created.password_hash != "secret123"
    assert "secret123" not in created.password_hash


def test_authenticate_returns_admin_role_for_admin_account(db_session):
    service = AuthService(db_session)
    service.register_admin("admin", "13800000000", "admin123")

    current_user = service.authenticate("admin", "admin123")

    assert current_user.username == "admin"
    assert current_user.role == "admin"


def test_authenticate_rejects_wrong_password(db_session):
    service = AuthService(db_session)
    service.register_user("alice", "13900000000", "right-pass")

    with pytest.raises(AuthenticationError, match="账号或密码错误"):
        service.authenticate("alice", "wrong-pass")


def test_authenticate_rejects_disabled_user(db_session):
    service = AuthService(db_session)
    service.register_user("alice", "13900000000", "right-pass")
    user = db_session.query(User).filter_by(username="alice").one()
    user.status = "disabled"
    db_session.commit()

    with pytest.raises(AuthenticationError, match="账号已被禁用"):
        service.authenticate("alice", "right-pass")


def test_register_user_validates_phone_and_password(db_session):
    service = AuthService(db_session)

    with pytest.raises(AuthenticationError, match="手机号不能为空"):
        service.register_user("bob", "", "secret123")

    with pytest.raises(AuthenticationError, match="手机号格式不正确"):
        service.register_user("bob", "123", "secret123")

    with pytest.raises(AuthenticationError, match="密码长度不能少于 6 位"):
        service.register_user("bob", "13700000000", "123")
