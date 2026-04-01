# Nanobot gateway Dockerfile
# Adapted from backend/Dockerfile and qwen-code-api/Dockerfile
# See https://docs.astral.sh/uv/guides/integration/docker/

# ---
# Stage 1: Build the application in the `/app` directory.
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}astral/uv:python3.14-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Omit development dependencies
ENV UV_NO_DEV=1

# Disable Python downloads - use the system interpreter across both images.
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Copy workspace packages
COPY --from=workspace mcp/ /app/mcp/
COPY --from=workspace nanobot-websocket-channel/ /app/nanobot-websocket-channel/
COPY --from=workspace nanobot/ /app/nanobot/

# Create virtual environment and install packages
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv /app/.venv && \
    VIRTUAL_ENV=/app/.venv uv pip install /app/mcp /app/nanobot-websocket-channel/mcp-webchat /app/nanobot-websocket-channel/nanobot-webchat && \
    VIRTUAL_ENV=/app/.venv uv pip install "nanobot-ai @ https://github.com/HKUDS/nanobot/archive/e7d371ec1e6531b28898ec2c869ef338e8dd46ec.zip"

# Copy the rest of nanobot source (config, entrypoint, workspace)
COPY . /app/nanobot/

# ---
# Stage 2: Use a final image without uv
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}python:3.14.2-slim-bookworm

# Set environment variables for Python and application
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8

# Accept runtime UID/GID for bind-mount development
ARG APP_UID=999
ARG APP_GID=999

# Setup non-root user with configurable UID/GID
# If APP_UID=0, we'll run as root (useful for development with host bind mounts)
RUN if [ "${APP_UID}" = "0" ]; then \
    echo "Running as root (APP_UID=0)"; \
    else \
    groupadd --system --gid ${APP_GID} nonroot \
    && useradd --system --gid ${APP_GID} --uid ${APP_UID} --create-home nonroot; \
    fi

# Copy the application from the builder
COPY --from=builder --chown=${APP_UID}:${APP_GID} /app /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"
ENV PYTHONPATH="/app/nanobot"

# Use the non-root user (or root if APP_UID=0)
USER ${APP_UID}:${APP_GID}

WORKDIR /app

# Run the entrypoint
CMD ["python", "/app/nanobot/entrypoint.py"]
