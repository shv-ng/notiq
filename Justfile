format:
  isort .
  ruff check --fix --unsafe-fixes
  ruff format .

dev:
  uv run fastapi dev

run:
  uv run fastapi run --host 0.0.0.0 --port 8000
