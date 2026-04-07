.PHONY: app worker beat tests lint lint-fix format format-check

app:
	uv run uvicorn app.main:app --reload
worker:
	uv run celery -A app.core.celery_app:celery_app worker -l info
beat:
	uv run celery -A app.core.celery_app:celery_app beat -l info
tests:
	uv run pytest
lint:
	uv run ruff check .
lint-fix:
	uv run ruff check . --fix
format:
	uv run ruff format .
format-check:
	uv run ruff format . --check