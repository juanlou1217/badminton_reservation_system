from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models import TimeSlot


class SlotService:
    def __init__(self, session: Session):
        self.session = session

    def list_available_slots(self, court_id: int | None = None, slot_date: date | None = None) -> list[TimeSlot]:
        query = self.session.query(TimeSlot).filter_by(status="available")
        if court_id is not None:
            query = query.filter_by(court_id=court_id)
        if slot_date is not None:
            query = query.filter_by(slot_date=slot_date)
        return query.order_by(TimeSlot.slot_date, TimeSlot.start_time).all()
