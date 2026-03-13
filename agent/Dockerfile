# Stage 1: Builder
# Build context is the REPO ROOT (set Railway root directory to "/" or blank,
# and Dockerfile path to "agent/Dockerfile").
FROM python:3.12-slim AS builder
WORKDIR /app
COPY agent/pyproject.toml .
COPY agent/src/ src/
RUN pip install --no-cache-dir .

# Stage 2: Runtime
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY agent/src/ src/
COPY agent/alembic/ alembic/
COPY agent/alembic.ini .
COPY neos-core/ neos-core/
RUN adduser --disabled-password --gecos "" neos && chown -R neos:neos /app
USER neos
CMD ["sanic", "neos_agent.main:create_app", "--host", "0.0.0.0", "--port", "8000", "--factory"]
