from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Court, TimeSlot, User


class AdminPermissionError(Exception):
    """Raised when a non-admin user tries to perform admin work."""


class AdminService:
    VALID_USER_STATUSES = {"normal", "disabled"}
    VALID_COURT_STATUSES = {"open", "closed"}

    def __init__(self, session: Session, current_user: User):
        self.session = session
        self.current_user = current_user

    def require_admin(self) -> None:
        if self.current_user.role != "admin":
            raise AdminPermissionError("需要管理员权限")

    def list_users(self) -> list[User]:
        self.require_admin()
        return self.session.query(User).order_by(User.id).all()

    def set_user_status(self, user_id: int, status: str) -> User:
        self.require_admin()
        if status not in self.VALID_USER_STATUSES:
            raise ValueError("用户状态不合法")
        user = self.session.get(User, user_id)
        if user is None:
            raise ValueError("用户不存在")
        user.status = status
        self._commit()
        self.session.refresh(user)
        return user

    def create_court(
        self,
        court_no: str,
        name: str,
        location: str,
        status: str = "open",
        remark: str = "",
    ) -> Court:
        self.require_admin()
        court_no = court_no.strip()
        name = name.strip()
        location = location.strip()
        if not court_no:
            raise ValueError("场地编号不能为空")
        if not name:
            raise ValueError("场地名称不能为空")
        if status not in self.VALID_COURT_STATUSES:
            raise ValueError("场地状态不合法")
        court = Court(
            court_no=court_no,
            name=name,
            location=location,
            status=status,
            remark=remark.strip(),
        )
        self.session.add(court)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ValueError("场地编号已存在") from exc
        self.session.refresh(court)
        return court

    def update_court_status(self, court_id: int, status: str) -> Court:
        self.require_admin()
        if status not in self.VALID_COURT_STATUSES:
            raise ValueError("场地状态不合法")
        court = self.session.get(Court, court_id)
        if court is None:
            raise ValueError("场地不存在")
        court.status = status
        self._commit()
        self.session.refresh(court)
        return court

    def generate_slots(
        self,
        court_id: int,
        start_date: date,
        end_date: date,
        time_ranges: list[tuple],
    ) -> list[TimeSlot]:
        self.require_admin()
        if start_date > end_date:
            raise ValueError("开始日期不能晚于结束日期")
        court = self.session.get(Court, court_id)
        if court is None:
            raise ValueError("场地不存在")
        generated: list[TimeSlot] = []
        current = start_date
        while current <= end_date:
            for start_time, end_time in time_ranges:
                if start_time >= end_time:
                    raise ValueError("时间段开始时间必须早于结束时间")
                exists = (
                    self.session.query(TimeSlot)
                    .filter_by(
                        court_id=court_id,
                        slot_date=current,
                        start_time=start_time,
                        end_time=end_time,
                    )
                    .one_or_none()
                )
                if exists is None:
                    slot = TimeSlot(
                        court_id=court_id,
                        slot_date=current,
                        start_time=start_time,
                        end_time=end_time,
                        status="available",
                    )
                    self.session.add(slot)
                    generated.append(slot)
            current += timedelta(days=1)
        self._commit()
        for slot in generated:
            self.session.refresh(slot)
        return generated

    def _commit(self) -> None:
        try:
            self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()
            raise
