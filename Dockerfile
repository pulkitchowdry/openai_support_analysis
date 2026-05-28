FROM python:3.11-slim AS backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/backend

COPY backend/pyproject.toml ./
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir .

COPY backend/ ./

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


FROM node:20-bookworm-slim AS frontend-deps

WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install


FROM node:20-bookworm-slim AS frontend-builder

WORKDIR /app/frontend
COPY --from=frontend-deps /app/frontend/node_modules ./node_modules
COPY frontend/ ./
RUN npm run build


FROM node:20-bookworm-slim AS frontend

ENV NODE_ENV=production

WORKDIR /app/frontend
COPY frontend/package.json ./
COPY --from=frontend-deps /app/frontend/node_modules ./node_modules
COPY --from=frontend-builder /app/frontend/.next ./.next
COPY frontend/next.config.mjs ./

EXPOSE 3000
CMD ["npm", "run", "start", "--", "--hostname", "0.0.0.0", "--port", "3000"]
