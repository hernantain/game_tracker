FROM node:22-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.5.24 /uv /usr/local/bin/uv
WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH"

# Dependencies first so this layer is cached until the lockfile changes.
# Only the default groups are installed; the `seed` group stays out of the image.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY backend/ backend/
COPY start.sh start.sh
RUN chmod +x start.sh
COPY --from=frontend-build /app/frontend/dist/ backend/static/

ENV PORT=8080
EXPOSE 8080
CMD ["./start.sh"]
