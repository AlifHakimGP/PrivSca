# No multi-stage build needed this time — there's no frontend build step
# at all (plain HTML/CSS/JS, served as-is), so this is a single, simple
# stage unlike push-dashboard's Dockerfile.
FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY static/ ./static/

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
