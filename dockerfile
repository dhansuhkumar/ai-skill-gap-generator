# ---- Builder Stage ----
# This stage installs dependencies, including build tools
FROM python:3.11-slim as builder

# Prevent Python from buffering logs & writing .pyc files
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Install system deps for building wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements-prod.txt .
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements-prod.txt


# ---- Final Stage ----
# This stage is the final, smaller image
FROM python:3.11-slim

# Prevent Python from buffering logs & writing .pyc files
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_ENV=production

# Set working directory
WORKDIR /app

# Copy wheels from builder stage and install them
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/*

# Copy app files
COPY backend/ ./backend/

# Expose the port Render expects
EXPOSE 5000

# Use uvicorn workers to support async Flask routes
CMD ["gunicorn", "--workers=1", "--worker-class", "uvicorn.workers.UvicornWorker", "--timeout=0", "--bind", "0.0.0.0:5000", "backend.run:app"]