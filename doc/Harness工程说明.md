# Harness 工程说明

本项目的 harness engineering 目标是把“能运行”变成“可检查、可复现、可交付”。它不改变课程设计技术栈，只补统一命令、自检脚本、CI 和验收记录。

## 统一命令

项目根目录提供 `Makefile`：

```bash
make setup
make doctor
make check
make run
```

常用命令说明：

| 命令 | 用途 |
| --- | --- |
| `make setup` | 创建 `.venv` 并安装 `requirements.txt` |
| `make doctor` | 检查 Python 版本、虚拟环境、依赖、关键文件、数据库环境变量 |
| `make doctor-mysql` | 在 `doctor` 基础上检查远程 MySQL 连通性和关键约束 |
| `make test` | 运行本地单元测试 |
| `make test-mysql` | 显式运行远程 MySQL 集成测试 |
| `make compile` | 编译检查 `app/`、`scripts/`、`main.py` |
| `make check` | 本地完整检查：`doctor + test + compile` |
| `make build-exe` | 使用 PyInstaller 打包桌面客户端 |

## 自检脚本

`scripts/doctor.py` 是项目自检入口：

```bash
.venv/bin/python scripts/doctor.py
.venv/bin/python scripts/doctor.py --mysql
```

默认检查：

- Python 版本是否满足项目要求。
- 是否在虚拟环境中运行。
- 第三方依赖是否可导入。
- 项目关键目录和文件是否存在。
- `.env` 或环境变量中的 `DB_*` 是否齐全。

`--mysql` 会额外检查：

- 能否连接远程 MySQL。
- `users`、`courts`、`time_slots`、`reservations`、`settings` 表是否存在。
- `reservations.active_slot_id` 生成列是否存在。
- `uq_reservations_active_slot` 唯一索引是否存在。

脚本输出会隐藏 `DB_PASSWORD`，避免真实密码出现在终端输出或日志中。

## CI

GitHub Actions 文件位于 `.github/workflows/tests.yml`。每次 push 或 pull request 会执行：

```bash
pytest -q
PYTHONPYCACHEPREFIX=/tmp/badminton_pycache python -m compileall -q app scripts main.py
```

CI 不连接远程 MySQL，不需要提交数据库密码。远程数据库验收仍通过本地 `make doctor-mysql` 和 `make test-mysql` 显式执行。

## 推荐验收顺序

```bash
make setup
cp .env.example .env
make doctor
make check
make doctor-mysql
make test-mysql
make run
```

如果 `make doctor` 失败，先处理环境变量、依赖或文件结构问题；如果只有 `make doctor-mysql` 失败，重点检查远程 MySQL 网络、账号密码和表结构。
