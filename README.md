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
│   └── init_admin.py
├── sql/
│   └── schema.sql
├── tests/
├── .env.example
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

3. 初始化数据库表。

```bash
python -c "from app.db import init_db; init_db()"
```

4. 创建管理员账号。

```bash
python scripts/init_admin.py
```

5. 启动程序。

```bash
python main.py
```

## 角色说明

- 普通用户注册时默认 `role=user`。
- 管理员账号通过 `scripts/init_admin.py` 或数据库初始化创建，`role=admin`。
- 登录成功后根据 `users.role` 打开不同 Tkinter 主窗口。

## 测试

```bash
pytest -q
```

测试使用 SQLAlchemy 内存数据库验证服务层行为；正式运行只连接 `.env` 配置的远程 MySQL。
