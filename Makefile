# Heathrow Punctuality Dashboard — developer tasks.
# `make` is optional; every command below is also shown in the README.

SHELL := pwsh
PY := py -3

.PHONY: help venv install db-up db-down migrate load dq test lint dashboard

help:
	@echo "Targets:"
	@echo "  venv        create virtualenv with uv"
	@echo "  install     install project + dev deps"
	@echo "  db-up       start PostgreSQL via docker compose"
	@echo "  db-down     stop PostgreSQL"
	@echo "  migrate     apply SQL schema + KPI views (psql or pipeline)"
	@echo "  load        run the full pipeline (download -> parse -> load -> dq)"
	@echo "  dq          run data-quality checks only"
	@echo "  test        run pytest"
	@echo "  lint        run ruff"
	@echo "  dashboard   run the Streamlit dashboard"

venv:
	uv venv

install: venv
	uv pip install -e ".[dev]"

db-up:
	docker compose up -d

db-down:
	docker compose down

load:
	$(PY) -m heathrow.cli run

dq:
	$(PY) -m heathrow.cli dq

test:
	$(PY) -m pytest

lint:
	$(PY) -m ruff check src tests

dashboard:
	$(PY) -m streamlit run app/Home.py