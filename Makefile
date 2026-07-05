# Makefile — common AXIOM developer commands. Run `make help` to list them.
.DEFAULT_GOAL := help
.PHONY: help install run run-dev test migrate lint build-ext build-dash setup-ebpf trace serve build-binary build-wheel publish publish-test

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install:  ## Install all Python dependencies (base + dev)
	pip install -e ".[dev]"

run:  ## Start full stack with Docker Compose
	docker compose up --build

run-dev:  ## Start backend in hot-reload mode (needs local Postgres or SQLite URL)
	uvicorn axiom.main:app --reload --host 0.0.0.0 --port 8000

serve:  ## Start backend via the axiom CLI (migrates then serves)
	axiom serve --port 8000

build-binary:  ## Build a standalone backend binary with PyInstaller (dist/axiom)
	pip install pyinstaller
	pyinstaller packaging/axiom.spec --distpath dist --workpath build/pyi --noconfirm

build-wheel:  ## Build sdist + wheel into dist/ (as loki-axiom)
	pip install --upgrade build
	rm -rf dist/*.whl dist/*.tar.gz
	python -m build

publish-test:  ## Upload to TestPyPI (verify before the real thing)
	pip install --upgrade twine
	twine upload --repository testpypi dist/loki_axiom-*

publish:  ## Upload to PyPI (needs a token; see PUBLISHING.md)
	pip install --upgrade twine
	twine upload dist/loki_axiom-*

test:  ## Run all tests with coverage
	pytest tests/ -v --cov=axiom --cov-report=term-missing

migrate:  ## Run Alembic migrations to latest
	alembic upgrade head

lint:  ## Run black + isort + mypy
	black axiom tests
	isort axiom tests
	mypy axiom

build-ext:  ## Build VS Code extension
	cd vscode-extension && npm install && npm run compile

build-dash:  ## Build React dashboard
	cd dashboard && npm install && npm run build

setup-ebpf:  ## Install BCC in WSL for the real eBPF tracer (run once)
	wsl.exe -e bash -lc "cd \$$(wslpath '$(CURDIR)') && bash scripts/setup_ebpf_wsl.sh"

trace:  ## Start the privileged eBPF tracer daemon inside WSL
	wsl.exe -e bash -lc "cd \$$(wslpath '$(CURDIR)') && sudo python3 -m axiom.workers.ebpf_worker --port 8770"
