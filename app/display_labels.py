from __future__ import annotations


ROLE_LABELS = {
    "admin": "管理员",
    "user": "普通用户",
}

USER_STATUS_LABELS = {
    "normal": "正常",
    "disabled": "已禁用",
}

COURT_STATUS_LABELS = {
    "open": "开放",
    "closed": "已停用",
}

SLOT_STATUS_LABELS = {
    "available": "可预约",
    "booked": "已预约",
    "disabled": "暂停开放",
}

RESERVATION_STATUS_LABELS = {
    "booked": "已预约",
    "cancelled": "已取消",
    "finished": "已核销",
}

RESERVATION_STATUS_FILTER_LABELS = ("全部", "已预约", "已取消", "已核销")
RESERVATION_STATUS_FILTER_VALUES = {
    "全部": "",
    "已预约": "booked",
    "已取消": "cancelled",
    "已核销": "finished",
}


def _label(mapping: dict[str, str], value: str) -> str:
    return mapping.get(value, value)


def role_label(value: str) -> str:
    return _label(ROLE_LABELS, value)


def user_status_label(value: str) -> str:
    return _label(USER_STATUS_LABELS, value)


def court_status_label(value: str) -> str:
    return _label(COURT_STATUS_LABELS, value)


def slot_status_label(value: str) -> str:
    return _label(SLOT_STATUS_LABELS, value)


def reservation_status_label(value: str) -> str:
    return _label(RESERVATION_STATUS_LABELS, value)


def reservation_status_value(label: str) -> str:
    return RESERVATION_STATUS_FILTER_VALUES.get(label, label)
