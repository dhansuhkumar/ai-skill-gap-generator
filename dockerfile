# ---- Base Image ----
FROM python:3.11-slim

# Prevent Python from buffering logs & writing .pyc files
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_ENV=production

# Set working directory
WORKDIR /app/backend

# Install system deps (only if needed for your libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy app files
COPY . .

# Expose the port Render expects
EXPOSE 5000

# ---- Optimization 1: Limit Gunicorn Workers ----
# Each worker duplicates your app (and ML model if loaded globally).
# Use 1 worker and 1 thread for low-RAM environments.
CMD ["gunicorn", "--workers=1", "--threads=1", "--timeout=0", "--bind", "0.0.0.0:5000", "backend.run:app"]
