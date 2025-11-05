FROM python:3.11-slim

WORKDIR /app
COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt


COPY . .

# Optional: Set environment variables here or in Render dashboard
ENV FLASK_ENV=production

# Expose port
EXPOSE 5000

# Run with Gunicorn (adjust if using factory)
CMD ["sh", "-c", "gunicorn backend.run:app --bind 0.0.0.0:${PORT:-5000}"]

