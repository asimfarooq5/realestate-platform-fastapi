.PHONY: install install-dev run dev seed migrate docker-build docker-up docker-migrate docker-seed test clean

DOCKER_COMPOSE = docker-compose

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

run:
	python3 run.py

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

seed:
	python -m app.seed

migrate:
	alembic upgrade head

migrate-new:
	alembic revision --autogenerate -m "$(m)"

docker-build:
	$(DOCKER_COMPOSE) build

docker-up:
	$(DOCKER_COMPOSE) up -d

docker-migrate:
	$(DOCKER_COMPOSE) run --rm api alembic upgrade head

docker-seed:
	$(DOCKER_COMPOSE) run --rm api python -m app.seed

test:
	pytest

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
