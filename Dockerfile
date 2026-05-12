FROM ghcr.io/astral-sh/uv:0.8.22 AS uv

FROM python:3.13-slim AS base

WORKDIR /app
RUN --mount=from=uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv export --frozen --no-emit-workspace --no-dev -o requirements.txt && \
    uv pip install --system -r requirements.txt

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
