from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Setting


class SettingsService:
    def __init__(self, session: Session):
        self.session = session

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
        setting = self.session.query(Setting).filter_by(setting_key=key).one_or_none()
        if setting is None:
            setting = Setting(setting_key=key, setting_value=value, remark=remark)
            self.session.add(setting)
        else:
            setting.setting_value = value
            setting.remark = remark
        self.session.commit()
        self.session.refresh(setting)
        return setting

    def list_settings(self) -> list[Setting]:
        return self.session.query(Setting).order_by(Setting.setting_key).all()
