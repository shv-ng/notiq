format:
  isort .
  ruff check --fix --unsafe-fixes
  ruff format .

dev:
  uv run fastapi dev

run:
  uv run fastapi run --host 0.0.0.0 --port 8000

makemigrate:
  uv run alembic revision --autogenerate 

migrate:
  uv run alembic upgrade head

celery:
  uv run celery -A app.tasks.event worker --loglevel=info
