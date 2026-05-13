from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Court, Reservation, TimeSlot, User


class StatsPermissionError(Exception):
    """Raised when a non-admin user tries to view global statistics."""


class StatsService:
    def __init__(self, session: Session, current_user: User):
        self.session = session
        self.current_user = current_user

    def reservation_summary(self) -> dict:
        if self.current_user.role != "admin":
            raise StatsPermissionError("需要管理员权限")
        total = self.session.query(func.count(Reservation.id)).scalar() or 0
        booked = self.session.query(func.count(Reservation.id)).filter_by(status="booked").scalar() or 0
        cancelled = self.session.query(func.count(Reservation.id)).filter_by(status="cancelled").scalar() or 0
        by_court_rows = (
            self.session.query(Court.name, func.count(Reservation.id))
            .join(Reservation, Reservation.court_id == Court.id)
            .group_by(Court.id, Court.name)
            .order_by(func.count(Reservation.id).desc())
            .all()
        )
        by_date_rows = (
            self.session.query(TimeSlot.slot_date, func.count(Reservation.id))
            .join(Reservation, Reservation.slot_id == TimeSlot.id)
            .group_by(TimeSlot.slot_date)
            .order_by(TimeSlot.slot_date)
            .all()
        )
        return {
            "total": total,
            "booked": booked,
            "cancelled": cancelled,
            "by_court": [{"court": name, "count": count} for name, count in by_court_rows],
            "by_date": [{"date": slot_date, "count": count} for slot_date, count in by_date_rows],
        }
