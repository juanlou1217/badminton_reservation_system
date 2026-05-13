from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db import get_engine


def main() -> None:
    try:
        with get_engine().connect() as connection:
            database = connection.execute(text("SELECT DATABASE()")).scalar_one()
            version = connection.execute(text("SELECT VERSION()")).scalar_one()
            tables = {row[0] for row in connection.execute(text("SHOW TABLES")).fetchall()}
            schema_ok = "未初始化"
            if "reservations" in tables:
                columns = {row[0] for row in connection.execute(text("SHOW COLUMNS FROM reservations")).fetchall()}
                indexes = {row[2] for row in connection.execute(text("SHOW INDEX FROM reservations")).fetchall()}
                if "active_slot_id" in columns and "uq_reservations_active_slot" in indexes:
                    schema_ok = "关键约束正常"
                else:
                    schema_ok = "缺少 active_slot_id 或有效预约唯一索引"
    except SQLAlchemyError as exc:
        raise SystemExit(f"数据库连接失败: {exc}") from exc
    print(f"数据库连接正常: database={database}, version={version}, schema={schema_ok}")


if __name__ == "__main__":
    main()
