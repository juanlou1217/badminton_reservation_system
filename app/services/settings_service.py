from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Setting, User


class SettingPermissionError(Exception):
    """Raised when a non-admin user tries to change system settings."""


class SettingError(Exception):
    """Raised when a setting cannot be saved."""


class SettingsService:
    def __init__(
        self,
        session: Session,
        current_user: User | None = None,
        allow_system_write: bool = False,
    ):
        self.session = session
        self.current_user = current_user
        self.allow_system_write = allow_system_write

    def get_value(self, key: str, default: str = "") -> str:
        setting = self.session.query(Setting).filter_by(setting_key=key).one_or_none()
        if setting is None:
            return default
        return setting.setting_value

    def get_int(self, key: str, default: int) -> int:
        value = self.get_value(key, str(default))
        try:
            return int(value)
        except ValueError:
            return default

    def set_value(self, key: str, value: str, remark: str = "") -> Setting:
        if not self.allow_system_write and (self.current_user is None or self.current_user.role != "admin"):
            raise SettingPermissionError("需要管理员权限")
        setting = self.session.query(Setting).filter_by(setting_key=key).one_or_none()
        if setting is None:
            setting = Setting(setting_key=key, setting_value=value, remark=remark)
            self.session.add(setting)
        else:
            setting.setting_value = value
            setting.remark = remark
        try:
            self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise SettingError("系统设置保存失败，请稍后重试") from exc
        self.session.refresh(setting)
        return setting

    def list_settings(self) -> list[Setting]:
        return self.session.query(Setting).order_by(Setting.setting_key).all()
