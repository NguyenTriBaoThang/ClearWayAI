.PHONY: help install dev dev-api dev-web test test-api test-web lint build clean compose-up compose-down

help:
	@echo "ClearWayAI Monorepo Commands:"
	@echo "  make install      Install Python and Node dependencies"
	@echo "  make dev          Run API and Web concurrently"
	@echo "  make dev-api      Run FastAPI server locally"
	@echo "  make dev-web      Run Vite frontend locally"
	@echo "  make test         Run all tests (Python + Web)"
	@echo "  make test-api     Run Pytest smoke and unit tests"
	@echo "  make test-web     Run Web tests"
	@echo "  make lint         Run linters (ruff, eslint)"
	@echo "  make build        Build all web applications and packages"
	@echo "  make compose-up   Start Docker containers"
	@echo "  make compose-down Stop Docker containers"

install:
	pip install -r requirements.txt
	npm install

dev:
	@echo "Starting ClearWayAI API (8000) and Web (5173/3000)..."
	npm run dev:all

dev-api:
	python -m uvicorn apps.api.src.main:app --reload --host 0.0.0.0 --port 8000

dev-web:
	npm --prefix apps/web run dev

test: test-api test-web

test-api:
	pytest -v

test-web:
	npm --prefix apps/web run test

lint:
	python -m ruff check . || true
	npm --prefix apps/web run lint || true

build:
	npm --prefix packages/shared run build || true
	npm --prefix apps/web run build

compose-up:
	docker compose up -d

compose-down:
	docker compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf apps/web/dist docs-site/dist packages/shared/dist
