# Stage 1: Builder
# Build context is the REPO ROOT (set Railway root directory to "/" or blank,
# and Dockerfile path to "Dockerfile").
# Multi-stage build for Railway deployment. Dependencies are locked in agent/uv.lock.
FROM python:3.12-slim AS builder
WORKDIR /app
COPY ./agent/pyproject.toml ./agent/uv.lock ./
COPY ./agent/src/ src/
RUN python -m pip install --no-cache-dir uv==0.9.18 \
    && uv sync --frozen --no-dev --no-editable

FROM builder AS test
ENV PATH="/app/.venv/bin:$PATH"
ENV NEOS_CORE_PATH="/app/neos-core"
RUN uv sync --frozen --extra dev --no-editable
COPY ./agent/tests/ agent/tests/
COPY ./agent/test_agent_e2e.py ./agent/test_agent_service_e2e.py ./agent/benchmark_skills.py agent/
COPY ./neos-core/ neos-core/
CMD ["pytest", "agent/tests", "-q"]

# Stage 2: Runtime
FROM python:3.12-slim
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"
COPY --from=builder /app/.venv /app/.venv
COPY ./agent/src/ src/
COPY ./agent/alembic/ alembic/
COPY ./agent/alembic.ini .
COPY ./neos-core/ neos-core/
RUN adduser --disabled-password --gecos "" neos && chown -R neos:neos /app
USER neos
CMD ["sh", "-c", "alembic upgrade head && exec sanic neos_agent.main:create_app --host 0.0.0.0 --port ${PORT:-8000} --factory --single-process"]
