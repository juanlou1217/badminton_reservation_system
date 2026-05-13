from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'admin')", name="chk_users_role"),
        CheckConstraint("status IN ('normal', 'disabled')", name="chk_users_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    reservations: Mapped[list["Reservation"]] = relationship(back_populates="user")


class Court(Base):
    __tablename__ = "courts"
    __table_args__ = (
        CheckConstraint("status IN ('open', 'closed')", name="chk_courts_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    court_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    remark: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    slots: Mapped[list["TimeSlot"]] = relationship(back_populates="court")
    reservations: Mapped[list["Reservation"]] = relationship(back_populates="court")


class TimeSlot(Base):
    __tablename__ = "time_slots"
    __table_args__ = (
        UniqueConstraint(
            "court_id",
            "slot_date",
            "start_time",
            "end_time",
            name="uq_time_slots_court_date_time",
        ),
        CheckConstraint("status IN ('available', 'booked', 'disabled')", name="chk_time_slots_status"),
        CheckConstraint("start_time < end_time", name="chk_time_slots_time_range"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    court_id: Mapped[int] = mapped_column(ForeignKey("courts.id"), nullable=False, index=True)
    slot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="available")

    court: Mapped[Court] = relationship(back_populates="slots")
    reservations: Mapped[list["Reservation"]] = relationship(back_populates="slot")


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (
        UniqueConstraint("active_slot_id", name="uq_reservations_active_slot"),
        CheckConstraint("status IN ('booked', 'cancelled', 'finished')", name="chk_reservations_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reservation_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    court_id: Mapped[int] = mapped_column(ForeignKey("courts.id"), nullable=False, index=True)
    slot_id: Mapped[int] = mapped_column(ForeignKey("time_slots.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="booked")
    active_slot_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        Computed("CASE WHEN status = 'booked' THEN slot_id ELSE NULL END", persisted=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship(back_populates="reservations")
    court: Mapped[Court] = relationship(back_populates="reservations")
    slot: Mapped[TimeSlot] = relationship(back_populates="reservations")


class Setting(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    setting_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    setting_value: Mapped[str] = mapped_column(String(255), nullable=False)
    remark: Mapped[str] = mapped_column(Text, nullable=False, default="")
