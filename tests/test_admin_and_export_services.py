from __future__ import annotations

from datetime import date, time
from pathlib import Path

import openpyxl
import pytest

from app.services.admin_service import AdminPermissionError, AdminService
from app.services.export_service import ExportPermissionError, ExportService
from app.services.reservation_service import ReservationService


def test_admin_service_rejects_non_admin(db_session, seeded_db):
    service = AdminService(db_session, seeded_db["user"])

    with pytest.raises(AdminPermissionError):
        service.list_users()


def test_admin_can_create_court_and_generate_slots(db_session, seeded_db):
    service = AdminService(db_session, seeded_db["admin"])

    court = service.create_court("C02", "二号场", "体育馆二层", "open", "")
    slots = service.generate_slots(
        court_id=court.id,
        start_date=date(2026, 5, 21),
        end_date=date(2026, 5, 21),
        time_ranges=[(time(8, 0), time(10, 0)), (time(10, 0), time(12, 0))],
    )

    assert court.court_no == "C02"
    assert len(slots) == 2


def test_admin_service_validates_court_input(db_session, seeded_db):
    service = AdminService(db_session, seeded_db["admin"])

    with pytest.raises(ValueError, match="场地编号不能为空"):
        service.create_court("", "二号场", "体育馆二层", "open", "")

    with pytest.raises(ValueError, match="场地状态不合法"):
        service.create_court("C02", "二号场", "体育馆二层", "broken", "")


def test_admin_can_update_court_details(db_session, seeded_db):
    service = AdminService(db_session, seeded_db["admin"])
    court = service.create_court("C02", "二号场", "体育馆二层", "open", "")

    updated = service.update_court(
        court.id,
        court_no="C02A",
        name="二号训练场",
        location="体育馆三层",
        status="closed",
        remark="维护中",
    )

    assert updated.court_no == "C02A"
    assert updated.name == "二号训练场"
    assert updated.location == "体育馆三层"
    assert updated.status == "closed"
    assert updated.remark == "维护中"


def test_admin_can_delete_unused_court(db_session, seeded_db):
    service = AdminService(db_session, seeded_db["admin"])
    court = service.create_court("C02", "二号场", "体育馆二层", "open", "")

    service.delete_court(court.id)

    assert db_session.get(type(court), court.id) is None


def test_admin_cannot_delete_court_with_slots(db_session, seeded_db):
    service = AdminService(db_session, seeded_db["admin"])

    with pytest.raises(ValueError, match="场地已有时间段"):
        service.delete_court(seeded_db["court"].id)


def test_admin_can_list_and_disable_available_slot(db_session, seeded_db):
    service = AdminService(db_session, seeded_db["admin"])

    slots = service.list_slots(slot_date=date(2026, 5, 20))
    updated = service.set_slot_status(seeded_db["slot"].id, "disabled")

    assert [slot.id for slot in slots] == [seeded_db["slot"].id]
    assert updated.status == "disabled"


def test_export_reservations_to_xlsx_creates_valid_workbook(tmp_path, db_session, seeded_db):
    ReservationService(db_session).create_reservation(
        user_id=seeded_db["user"].id,
        slot_id=seeded_db["slot"].id,
    )
    output = tmp_path / "reservations.xlsx"

    ExportService(db_session, seeded_db["admin"]).export_reservations_to_xlsx(output)

    assert output.exists()
    workbook = openpyxl.load_workbook(output)
    sheet = workbook.active
    assert sheet["A1"].value == "预约编号"
    assert sheet.max_row == 2


def test_export_service_rejects_non_admin(tmp_path, db_session, seeded_db):
    output = tmp_path / "reservations.xlsx"

    with pytest.raises(ExportPermissionError):
        ExportService(db_session, seeded_db["user"]).export_reservations_to_xlsx(output)
