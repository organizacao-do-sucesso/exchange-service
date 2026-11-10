# syntax=docker/dockerfile:1
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --no-install-project

COPY store ./store
RUN useradd --system --uid 10001 app
USER app
EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "store.exchange.application:app", "--host", "0.0.0.0", "--port", "8000"]
