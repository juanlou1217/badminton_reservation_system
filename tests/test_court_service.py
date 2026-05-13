from __future__ import annotations

from app.models import Court
from app.services.court_service import CourtService


def test_list_open_courts_filters_by_keyword(db_session, seeded_db):
    db_session.add_all(
        [
            Court(court_no="C02", name="二号训练场", location="体育馆二层", status="open", remark=""),
            Court(court_no="C03", name="三号场", location="体育馆三层", status="closed", remark=""),
        ]
    )
    db_session.commit()

    courts = CourtService(db_session).list_open_courts("训练")

    assert [court.court_no for court in courts] == ["C02"]
