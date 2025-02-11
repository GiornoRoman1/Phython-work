# Use specific version for security
FROM python:3.9-slim

# Create non-root user
RUN useradd -m -r -u 1001 appuser

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set secure Python options
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Run with explicit host and port
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:8080", "--workers", "3", "app:app"]