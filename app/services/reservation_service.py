from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session, joinedload

from app.models import Reservation, TimeSlot
from app.services.settings_service import SettingsService


class ReservationError(Exception):
    """Raised when a reservation operation violates business rules."""


class ReservationService:
    def __init__(self, session: Session):
        self.session = session

    def create_reservation(self, user_id: int, slot_id: int) -> Reservation:
        slot = self.session.get(TimeSlot, slot_id)
        if slot is None:
            raise ReservationError("时间段不存在")
        if slot.status != "available":
            raise ReservationError("时间段已被预约")
        exists = (
            self.session.query(Reservation)
            .filter_by(slot_id=slot_id, status="booked")
            .one_or_none()
        )
        if exists is not None:
            raise ReservationError("时间段已被预约")
        max_daily = SettingsService(self.session).get_int("max_daily_reservations", 2)
        daily_count = (
            self.session.query(Reservation)
            .join(TimeSlot, Reservation.slot_id == TimeSlot.id)
            .filter(
                Reservation.user_id == user_id,
                Reservation.status == "booked",
                TimeSlot.slot_date == slot.slot_date,
            )
            .count()
        )
        if daily_count >= max_daily:
            raise ReservationError("超过每日预约次数限制")
        reservation = Reservation(
            reservation_no=self._new_reservation_no(),
            user_id=user_id,
            court_id=slot.court_id,
            slot_id=slot_id,
            status="booked",
        )
        slot.status = "booked"
        self.session.add(reservation)
        self.session.commit()
        self.session.refresh(reservation)
        return reservation

    def cancel_reservation(
        self,
        reservation_id: int,
        current_user_id: int,
        is_admin: bool = False,
    ) -> Reservation:
        reservation = self.session.get(Reservation, reservation_id)
        if reservation is None:
            raise ReservationError("预约不存在")
        if reservation.status != "booked":
            raise ReservationError("预约已取消或已完成")
        if not is_admin and reservation.user_id != current_user_id:
            raise ReservationError("只能取消自己的预约")
        reservation.status = "cancelled"
        reservation.cancelled_at = datetime.now()
        slot = self.session.get(TimeSlot, reservation.slot_id)
        if slot is not None:
            slot.status = "available"
        self.session.commit()
        self.session.refresh(reservation)
        return reservation

    def list_user_reservations(self, user_id: int) -> list[Reservation]:
        return (
            self.session.query(Reservation)
            .options(joinedload(Reservation.court), joinedload(Reservation.slot))
            .filter_by(user_id=user_id)
            .order_by(Reservation.created_at.desc())
            .all()
        )

    def list_all_reservations(self) -> list[Reservation]:
        return (
            self.session.query(Reservation)
            .options(
                joinedload(Reservation.user),
                joinedload(Reservation.court),
                joinedload(Reservation.slot),
            )
            .order_by(Reservation.created_at.desc())
            .all()
        )

    def _new_reservation_no(self) -> str:
        return "R" + datetime.now().strftime("%Y%m%d%H%M%S") + uuid4().hex[:6].upper()
