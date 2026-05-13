PYTHON ?= .venv/bin/python
PYTEST ?= .venv/bin/pytest
PYINSTALLER ?= .venv/bin/pyinstaller

.PHONY: help setup doctor doctor-mysql test test-mysql compile check run build-exe clean

help:
	@echo "可用命令:"
	@echo "  make setup        创建虚拟环境并安装依赖"
	@echo "  make doctor       本地工程化自检，不连接远程 MySQL"
	@echo "  make doctor-mysql 本地自检并检查远程 MySQL"
	@echo "  make test         运行本地 pytest"
	@echo "  make test-mysql   运行远程 MySQL 可选集成测试"
	@echo "  make compile      编译检查 app/scripts/main.py"
	@echo "  make check        本地完整检查：doctor + test + compile"
	@echo "  make run          启动 Tkinter 客户端"
	@echo "  make build-exe    使用 PyInstaller 打包"

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

doctor:
	$(PYTHON) scripts/doctor.py

doctor-mysql:
	$(PYTHON) scripts/doctor.py --mysql

test:
	$(PYTEST) -q

test-mysql:
	RUN_MYSQL_TESTS=1 $(PYTEST) tests/test_mysql_connection_optional.py -q

compile:
	PYTHONPYCACHEPREFIX=/private/tmp/badminton_pycache $(PYTHON) -m compileall -q app scripts main.py

check: doctor test compile

run:
	$(PYTHON) main.py

build-exe:
	$(PYINSTALLER) -F -w main.py -n 体育馆羽毛球预约系统

clean:
	rm -rf .pytest_cache build dist
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
