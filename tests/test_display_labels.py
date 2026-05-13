from __future__ import annotations

from app.display_labels import (
    court_status_label,
    reservation_status_label,
    reservation_status_value,
    role_label,
    slot_status_label,
    user_status_label,
)


def test_display_labels_translate_internal_values_to_chinese():
    assert role_label("admin") == "管理员"
    assert role_label("user") == "普通用户"
    assert user_status_label("normal") == "正常"
    assert user_status_label("disabled") == "已禁用"
    assert court_status_label("open") == "开放"
    assert court_status_label("closed") == "已停用"
    assert slot_status_label("available") == "可预约"
    assert slot_status_label("booked") == "已预约"
    assert reservation_status_label("cancelled") == "已取消"
    assert reservation_status_label("finished") == "已核销"


def test_reservation_status_filter_labels_map_back_to_internal_values():
    assert reservation_status_value("全部") == ""
    assert reservation_status_value("已预约") == "booked"
    assert reservation_status_value("已取消") == "cancelled"
    assert reservation_status_value("已核销") == "finished"
