# 体育馆羽毛球预约系统

Python A 类课程设计项目：C/S 桌面管理系统，客户端使用 Tkinter，数据库使用远程 MySQL，数据访问层使用 SQLAlchemy ORM。

## 技术栈

- Python
- Tkinter + ttk
- SQLAlchemy ORM
- PyMySQL
- python-dotenv
- Werkzeug
- tkcalendar
- openpyxl
- pytest
- PyInstaller

## 项目结构

```text
badminton_reservation_system/
├── app/
│   ├── config.py
│   ├── db.py
│   ├── models.py
│   ├── services/
│   └── ui/
├── scripts/
│   ├── doctor.py
│   └── check_db_connection.py
├── sql/
│   └── init.sql
├── doc/
│   ├── 课程设计报告草稿.md
│   ├── 测试用例与运行记录.md
│   ├── 运行与打包说明.md
│   ├── Harness工程说明.md
│   └── templates/
├── tests/
├── .github/workflows/tests.yml
├── .env.example
├── Makefile
├── requirements.txt
├── build_exe.md
└── main.py
```

## 本地运行

1. 创建虚拟环境。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. 创建 `.env`。

```bash
cp .env.example .env
```

把 `.env` 中的 `DB_PASSWORD` 改为真实密码。

3. 初始化数据库。`sql/init.sql` 会一次性创建表结构、演示账号、默认设置、场地和当天时间段。

```bash
mysql -h juanlou.top -P 3306 -u juanlou -p juanlou < sql/init.sql
```

4. 检查数据库连接和关键约束。

```bash
python scripts/check_db_connection.py
```

5. 启动程序。

```bash
python main.py
```

也可以使用统一工程命令：

```bash
make doctor
make check
make run
```

## 角色说明

- 普通用户注册时默认 `role=user`。
- `sql/init.sql` 已包含课程演示账号，执行后可直接使用演示管理员登录；正式环境应重置密码。
- 登录成功后根据 `users.role` 打开不同 Tkinter 主窗口。
- 管理员可维护公告和每日预约次数限制，普通用户预约时会校验该限制。
- 用户到场后，管理员可在预约管理中核销预约，内部状态从 `booked` 变为 `finished`。

## 文档材料

课程设计文档集中放在 `doc/`：

- 报告草稿
- 测试用例与运行记录
- 运行与打包说明
- 数据库设计说明
- Harness 工程说明
- 截图清单
- 老师提供的 Word 模板备份

## 测试

```bash
pytest -q
```

测试使用 SQLAlchemy 内存数据库验证服务层行为；正式运行只连接 `.env` 配置的远程 MySQL。远程数据库连通性可通过 `python scripts/check_db_connection.py` 检查。

可选远程 MySQL 集成测试会检查远程库连通性、项目表、`reservations.active_slot_id` 生成列和有效预约唯一索引：

```bash
RUN_MYSQL_TESTS=1 pytest tests/test_mysql_connection_optional.py -q
```

工程化自检入口：

```bash
python scripts/doctor.py
python scripts/doctor.py --mysql
```

## 关键实现说明

- 预约创建使用数据库条件更新抢占时间段：只有 `time_slots.status='available'` 时才会更新为 `booked`，避免两个客户端同时预约同一时间段。
- `reservations.active_slot_id` 生成列配合 `uq_reservations_active_slot` 唯一索引，从数据库层限制同一时间段只能存在一条有效预约。
- 管理员服务、统计、导出、系统设置写入、全部预约查询都在服务层校验当前用户角色，不能只依赖 UI 入口。
- 取消预约接收当前用户对象，服务层根据 `role` 判断是否允许管理员取消他人预约。
- 核销预约只允许管理员执行；已核销预约不能再次取消，且会计入每日预约次数限制。
- 服务层在数据库提交失败时执行 rollback，避免 session 留在不可继续使用状态。
