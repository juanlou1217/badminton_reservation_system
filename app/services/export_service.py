from __future__ import annotations

from pathlib import Path

import openpyxl
from sqlalchemy.orm import Session

from app.services.reservation_service import ReservationService


class ExportService:
    def __init__(self, session: Session):
        self.session = session

    def export_reservations_to_xlsx(self, output_path: str | Path) -> Path:
        output = Path(output_path)
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "预约记录"
        sheet.append(["预约编号", "用户", "场地", "日期", "开始时间", "结束时间", "状态"])
        reservations = ReservationService(self.session).list_all_reservations()
        for item in reservations:
            sheet.append(
                [
                    item.reservation_no,
                    item.user.username if item.user else "",
                    item.court.name if item.court else "",
                    item.slot.slot_date.isoformat() if item.slot else "",
                    str(item.slot.start_time) if item.slot else "",
                    str(item.slot.end_time) if item.slot else "",
                    item.status,
                ]
            )
        workbook.save(output)
        return output
