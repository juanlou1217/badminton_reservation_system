from __future__ import annotations

from app.ui.admin_window import format_stats_summary


def test_format_stats_summary_uses_actual_line_breaks():
    summary = {
        "total": 0,
        "booked": 0,
        "cancelled": 0,
        "finished": 0,
        "by_court": [],
        "by_date": [],
    }

    text = format_stats_summary(summary)

    assert "\\n" not in text
    assert "预约总数：0\n有效预约：0" in text
    assert "已核销：0" in text
