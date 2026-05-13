from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Court, TimeSlot, User


class AdminPermissionError(Exception):
    """Raised when a non-admin user tries to perform admin work."""


class AdminService:
    def __init__(self, session: Session):
        self.session = session

    def require_admin(self, user: User) -> None:
        if user.role != "admin":
            raise AdminPermissionError("需要管理员权限")

    def list_users(self) -> list[User]:
        return self.session.query(User).order_by(User.id).all()

    def set_user_status(self, user_id: int, status: str) -> User:
        user = self.session.get(User, user_id)
        if user is None:
            raise ValueError("用户不存在")
        user.status = status
        self.session.commit()
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
        court = Court(
            court_no=court_no.strip(),
            name=name.strip(),
            location=location.strip(),
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
        court = self.session.get(Court, court_id)
        if court is None:
            raise ValueError("场地不存在")
        court.status = status
        self.session.commit()
        self.session.refresh(court)
        return court

    def generate_slots(
        self,
        court_id: int,
        start_date: date,
        end_date: date,
        time_ranges: list[tuple],
    ) -> list[TimeSlot]:
        court = self.session.get(Court, court_id)
        if court is None:
            raise ValueError("场地不存在")
        generated: list[TimeSlot] = []
        current = start_date
        while current <= end_date:
            for start_time, end_time in time_ranges:
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
        self.session.commit()
        for slot in generated:
            self.session.refresh(slot)
        return generated
