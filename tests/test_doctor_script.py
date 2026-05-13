from __future__ import annotations

from scripts.doctor import check_env_vars, check_imports, mask_secret


def test_mask_secret_hides_database_password():
    assert mask_secret("abcdef123456") == "ab********56"
    assert mask_secret("short") == "*****"
    assert mask_secret("") == ""


def test_check_env_vars_reports_missing_without_leaking_password(monkeypatch):
    monkeypatch.setenv("DB_HOST", "juanlou.top")
    monkeypatch.setenv("DB_PORT", "3306")
    monkeypatch.setenv("DB_USER", "juanlou")
    monkeypatch.setenv("DB_PASSWORD", "super-secret-password")
    monkeypatch.delenv("DB_NAME", raising=False)

    result = check_env_vars()

    assert not result.ok
    assert "DB_NAME" in result.message
    assert "super-secret-password" not in result.details
    assert "su*****************rd" in result.details


def test_check_imports_accepts_installed_modules_and_reports_missing():
    result = check_imports(["pathlib", "module_that_should_not_exist_987654"])

    assert not result.ok
    assert "module_that_should_not_exist_987654" in result.message
