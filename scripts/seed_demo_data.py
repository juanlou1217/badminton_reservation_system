from __future__ import annotations

from datetime import date, time
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db import SessionLocal, init_db
from app.models import Court, TimeSlot
from app.services.settings_service import SettingsService


def main() -> None:
    init_db()
    session = SessionLocal()
    try:
        courts = [
            ("C01", "一号场", "体育馆一层东侧"),
            ("C02", "二号场", "体育馆一层西侧"),
            ("C03", "三号场", "体育馆二层"),
        ]
        for court_no, name, location in courts:
            exists = session.query(Court).filter_by(court_no=court_no).one_or_none()
            if exists is None:
                session.add(Court(court_no=court_no, name=name, location=location, status="open", remark="演示数据"))
        session.commit()
        ranges = [(time(8, 0), time(10, 0)), (time(10, 0), time(12, 0)), (time(14, 0), time(16, 0)), (time(16, 0), time(18, 0))]
        for court in session.query(Court).all():
            for start_time, end_time in ranges:
                exists = (
                    session.query(TimeSlot)
                    .filter_by(
                        court_id=court.id,
                        slot_date=date.today(),
                        start_time=start_time,
                        end_time=end_time,
                    )
                    .one_or_none()
                )
                if exists is None:
                    session.add(
                        TimeSlot(
                            court_id=court.id,
                            slot_date=date.today(),
                            start_time=start_time,
                            end_time=end_time,
                            status="available",
                        )
                    )
        settings = SettingsService(session, allow_system_write=True)
        settings.set_value("max_daily_reservations", "2", "单个用户每天最多预约次数")
        settings.set_value("announcement", "欢迎使用体育馆羽毛球预约系统。", "系统公告")
        session.commit()
    finally:
        session.close()
    print("演示数据初始化完成")


if __name__ == "__main__":
    main()
