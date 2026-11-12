# Dockerfile / root / Node 24 + Python 3.12 / Render web service for LearnPlay
FROM node:24-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=frontend-build /frontend/dist ./learnplay/static
EXPOSE 10000
CMD ["sh", "-c", "python init_db.py && exec gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 2 wsgi:app"]
