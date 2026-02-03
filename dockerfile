FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS base

ARG USER_ID=1000
ARG GROUP_ID=1000

RUN groupadd --system --gid ${GROUP_ID} non-root \
    && useradd --system --gid ${GROUP_ID} --uid ${USER_ID} --create-home non-root

WORKDIR /src

ENV UV_COMPILE_BYTECODE=1
ENV UV_NO_DEV=1
ENV UV_TOOL_BIN_DIR=/usr/local/bin
ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

COPY pyproject.toml uv.lock ./
COPY src/ ./src/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked \
    && chown -R ${USER_ID}:${GROUP_ID} /src/.venv

ENV PATH="/src/.venv/bin:$PATH"

USER non-root

# stages

FROM base AS bot
CMD ["python", "-m", "src.main"]


FROM base AS alembic
COPY migrations/ ./migrations/
CMD ["alembic", "upgrade", "head"]
