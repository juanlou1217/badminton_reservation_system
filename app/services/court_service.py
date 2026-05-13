from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Court


class CourtService:
    def __init__(self, session: Session):
        self.session = session

    def list_open_courts(self, keyword: str = "") -> list[Court]:
        query = self.session.query(Court).filter_by(status="open")
        keyword = keyword.strip()
        if keyword:
            like = f"%{keyword}%"
            query = query.filter((Court.court_no.like(like)) | (Court.name.like(like)))
        return query.order_by(Court.court_no).all()

    def search_courts(self, keyword: str = "") -> list[Court]:
        query = self.session.query(Court)
        keyword = keyword.strip()
        if keyword:
            like = f"%{keyword}%"
            query = query.filter((Court.court_no.like(like)) | (Court.name.like(like)))
        return query.order_by(Court.court_no).all()
