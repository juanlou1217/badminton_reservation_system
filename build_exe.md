# 打包为 exe

Windows 环境下执行：

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pyinstaller -F -w main.py -n 体育馆羽毛球预约系统
```

生成文件位置：

```text
dist/体育馆羽毛球预约系统.exe
```

打包前确认：

- `.env` 中配置了远程 MySQL 连接信息。
- 目标电脑可以访问 `juanlou.top:3306`。
- 已执行 `sql/init.sql`，数据库中已有表结构、演示账号、默认设置、场地和当天时间段。
- 已运行 `python scripts/check_db_connection.py`，确认远程 MySQL 连接和关键约束正常。
- 如果需要分发给其他电脑，需一并提供 `.env` 或在目标电脑配置环境变量。
