from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.models import Reservation, TimeSlot, User
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
                Reservation.status.in_(("booked", "finished")),
                TimeSlot.slot_date == slot.slot_date,
            )
            .count()
        )
        if daily_count >= max_daily:
            raise ReservationError("超过每日预约次数限制")
        claimed = self.session.execute(
            update(TimeSlot)
            .where(TimeSlot.id == slot_id, TimeSlot.status == "available")
            .values(status="booked")
        )
        if claimed.rowcount != 1:
            self.session.rollback()
            raise ReservationError("时间段已被预约")
        reservation = Reservation(
            reservation_no=self._new_reservation_no(),
            user_id=user_id,
            court_id=slot.court_id,
            slot_id=slot_id,
            status="booked",
        )
        self.session.add(reservation)
        self._commit()
        self.session.refresh(reservation)
        return reservation

    def cancel_reservation(
        self,
        reservation_id: int,
        current_user: User,
    ) -> Reservation:
        reservation = self.session.get(Reservation, reservation_id)
        if reservation is None:
            raise ReservationError("预约不存在")
        if reservation.status != "booked":
            raise ReservationError("预约已取消或已完成")
        if current_user.role != "admin" and reservation.user_id != current_user.id:
            raise ReservationError("只能取消自己的预约")
        reservation.status = "cancelled"
        reservation.cancelled_at = datetime.now()
        slot = self.session.get(TimeSlot, reservation.slot_id)
        if slot is not None:
            slot.status = "available"
        self._commit()
        self.session.refresh(reservation)
        return reservation

    def verify_reservation(
        self,
        reservation_id: int,
        current_user: User,
    ) -> Reservation:
        if current_user.role != "admin":
            raise ReservationError("需要管理员权限")
        reservation = self.session.get(Reservation, reservation_id)
        if reservation is None:
            raise ReservationError("预约不存在")
        if reservation.status != "booked":
            raise ReservationError("只有已预约状态可以核销")
        reservation.status = "finished"
        self._commit()
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

    def list_all_reservations(
        self,
        current_user: User,
        username: str = "",
        status: str = "",
        slot_date=None,
    ) -> list[Reservation]:
        if current_user.role != "admin":
            raise ReservationError("需要管理员权限")
        query = (
            self.session.query(Reservation)
            .options(
                joinedload(Reservation.user),
                joinedload(Reservation.court),
                joinedload(Reservation.slot),
            )
        )
        username = username.strip()
        if username:
            query = query.join(User, Reservation.user_id == User.id).filter(User.username.contains(username))
        if status:
            query = query.filter(Reservation.status == status)
        if slot_date is not None:
            query = query.join(TimeSlot, Reservation.slot_id == TimeSlot.id).filter(TimeSlot.slot_date == slot_date)
        return query.order_by(Reservation.created_at.desc()).all()

    def _new_reservation_no(self) -> str:
        return "R" + datetime.now().strftime("%Y%m%d%H%M%S") + uuid4().hex[:6].upper()

    def _commit(self) -> None:
        try:
            self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise ReservationError("数据库操作失败，请稍后重试") from exc
