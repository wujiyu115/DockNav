# Stage 1: Frontend
FROM --platform=$BUILDPLATFORM oven/bun:1-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json ./
RUN --mount=type=cache,target=/root/.bun/install/cache bun install
COPY frontend/ ./
RUN bun run build

# Stage 2: Production
FROM python:3.11-slim AS production
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
COPY backend/requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/uv uv pip install --system -r requirements.txt
COPY backend/ ./
COPY --from=frontend-build /app/frontend/dist ./frontend/dist
ENV FRONTEND=/app/frontend/dist
EXPOSE 5100
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5100/api/health')" || exit 1
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5100"]
