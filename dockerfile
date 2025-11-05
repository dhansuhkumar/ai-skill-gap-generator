FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Optional: Set environment variables here or in Render dashboard
ENV FLASK_ENV=production

# Expose port
EXPOSE 5000

# Run with Gunicorn (adjust if using factory)
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "backend.run:app"]
