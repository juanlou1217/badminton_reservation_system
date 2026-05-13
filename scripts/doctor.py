from __future__ import annotations

import argparse
import importlib
import os
import platform
import sys
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db import get_engine


REQUIRED_ENV_VARS = ("DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME")
REQUIRED_IMPORTS = (
    "sqlalchemy",
    "pymysql",
    "dotenv",
    "werkzeug",
    "tkcalendar",
    "openpyxl",
    "pytest",
    "PyInstaller",
)
REQUIRED_PATHS = (
    "app",
    "app/models.py",
    "app/db.py",
    "app/services",
    "app/ui",
    "sql/init.sql",
    "tests",
    "pytest.ini",
    "requirements.txt",
    "README.md",
)


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    message: str
    details: str = ""


def mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 6:
        return "*" * len(value)
    return f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"


def check_python() -> CheckResult:
    version = platform.python_version()
    ok = sys.version_info >= (3, 9)
    return CheckResult(
        name="python",
        ok=ok,
        message=f"Python {version}" if ok else f"Python {version}，建议使用 3.9 或更高版本",
    )


def check_virtualenv() -> CheckResult:
    in_venv = sys.prefix != sys.base_prefix or bool(os.getenv("VIRTUAL_ENV"))
    return CheckResult(
        name="virtualenv",
        ok=in_venv,
        message="已在虚拟环境中运行" if in_venv else "当前不在 Python 虚拟环境中",
    )


def check_imports(modules: list[str] | tuple[str, ...] = REQUIRED_IMPORTS) -> CheckResult:
    missing: list[str] = []
    for module in modules:
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(module)
    if missing:
        return CheckResult("imports", False, "缺少依赖: " + ", ".join(missing))
    return CheckResult("imports", True, "第三方依赖导入正常")


def check_env_vars(required: tuple[str, ...] = REQUIRED_ENV_VARS) -> CheckResult:
    missing = [name for name in required if not os.getenv(name)]
    details = "\n".join(
        f"{name}={mask_secret(os.getenv(name, '')) if name == 'DB_PASSWORD' else os.getenv(name, '')}"
        for name in required
    )
    if missing:
        return CheckResult("env", False, "缺少环境变量: " + ", ".join(missing), details)
    return CheckResult("env", True, "数据库环境变量已配置", details)


def check_project_paths(root: Path | None = None) -> CheckResult:
    project_root = root or Path(__file__).resolve().parents[1]
    missing = [path for path in REQUIRED_PATHS if not (project_root / path).exists()]
    if missing:
        return CheckResult("paths", False, "缺少项目文件: " + ", ".join(missing))
    return CheckResult("paths", True, "项目结构关键文件完整")


def check_mysql() -> CheckResult:
    try:
        with get_engine().connect() as connection:
            database = connection.execute(text("SELECT DATABASE()")).scalar_one()
            tables = {row[0] for row in connection.execute(text("SHOW TABLES")).fetchall()}
            columns = {row[0] for row in connection.execute(text("SHOW COLUMNS FROM reservations")).fetchall()}
            indexes = {row[2] for row in connection.execute(text("SHOW INDEX FROM reservations")).fetchall()}
    except SQLAlchemyError as exc:
        return CheckResult("mysql", False, "远程 MySQL 连接或结构检查失败", str(exc))

    expected_tables = {"users", "courts", "time_slots", "reservations", "settings"}
    if not expected_tables.issubset(tables):
        return CheckResult("mysql", False, "远程 MySQL 缺少项目表", f"database={database}")
    if "active_slot_id" not in columns or "uq_reservations_active_slot" not in indexes:
        return CheckResult("mysql", False, "远程 MySQL 缺少有效预约唯一约束", f"database={database}")
    return CheckResult("mysql", True, f"远程 MySQL 正常: database={database}")


def render_result(result: CheckResult) -> str:
    mark = "OK" if result.ok else "FAIL"
    text = f"[{mark}] {result.name}: {result.message}"
    if result.details:
        text += f"\n{result.details}"
    return text


def run_checks(include_mysql: bool = False) -> list[CheckResult]:
    checks = [
        check_python(),
        check_virtualenv(),
        check_imports(),
        check_project_paths(),
        check_env_vars(),
    ]
    if include_mysql:
        checks.append(check_mysql())
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="体育馆羽毛球预约系统工程化自检")
    parser.add_argument("--mysql", action="store_true", help="同时检查远程 MySQL 连通性和关键约束")
    args = parser.parse_args()

    results = run_checks(include_mysql=args.mysql)
    for result in results:
        print(render_result(result))
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
