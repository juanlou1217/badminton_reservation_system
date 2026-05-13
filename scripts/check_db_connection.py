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
    except SQLAlchemyError as exc:
        raise SystemExit(f"数据库连接失败: {exc}") from exc
    print(f"数据库连接正常: database={database}, version={version}")


if __name__ == "__main__":
    main()
