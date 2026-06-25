# Builder
FROM ghcr.io/astral-sh/uv:python3.13-alpine AS builder

ENV UV_COMPILE_BYTECODE=1 
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /code

RUN --mount=type=cache,target=/root/.cache/uv \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  uv sync --locked --no-install-project

COPY . /code
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --locked

# Runtime
FROM python:3.13-alpine

RUN addgroup -S nonrootgroup && adduser -S nonroot -G nonrootgroup

COPY --from=builder --chown=nonrootgroup:nonroot /code /code

ENV PATH="/code/.venv/bin:$PATH"

USER nonroot

WORKDIR /code

CMD ["python3", "main.py"]
