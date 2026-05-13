from __future__ import annotations

from datetime import date, time

import pytest

from app.models import TimeSlot
from app.services.reservation_service import ReservationService
from app.services.settings_service import SettingPermissionError, SettingsService
from app.services.stats_service import StatsPermissionError, StatsService


def test_settings_service_returns_default_then_persisted_value(db_session, seeded_db):
    service = SettingsService(db_session, seeded_db["admin"])

    assert service.get_int("max_daily_reservations", 2) == 2

    service.set_value("max_daily_reservations", "3", "每日最大预约次数")

    assert service.get_int("max_daily_reservations", 2) == 3


def test_settings_service_rejects_non_admin_writer(db_session, seeded_db):
    service = SettingsService(db_session, seeded_db["user"])

    with pytest.raises(SettingPermissionError):
        service.set_value("announcement", "闭馆通知", "系统公告")


def test_settings_service_rejects_missing_writer(db_session):
    service = SettingsService(db_session)

    with pytest.raises(SettingPermissionError):
        service.set_value("announcement", "闭馆通知", "系统公告")


def test_stats_service_summarizes_reservations(db_session, seeded_db):
    second_slot = TimeSlot(
        court_id=seeded_db["court"].id,
        slot_date=date(2026, 5, 21),
        start_time=time(8, 0),
        end_time=time(10, 0),
        status="available",
    )
    db_session.add(second_slot)
    db_session.commit()
    reservation_service = ReservationService(db_session)
    reservation = reservation_service.create_reservation(seeded_db["user"].id, seeded_db["slot"].id)
    reservation_service.create_reservation(seeded_db["user"].id, second_slot.id)
    reservation_service.verify_reservation(reservation.id, seeded_db["admin"])

    summary = StatsService(db_session, seeded_db["admin"]).reservation_summary()

    assert summary["total"] == 2
    assert summary["booked"] == 1
    assert summary["cancelled"] == 0
    assert summary["finished"] == 1
    assert summary["by_court"][0]["court"] == "一号场"
    assert summary["by_court"][0]["count"] == 2


def test_stats_service_rejects_non_admin(db_session, seeded_db):
    service = StatsService(db_session, seeded_db["user"])

    with pytest.raises(StatsPermissionError):
        service.reservation_summary()
