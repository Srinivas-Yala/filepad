# Use a lightweight Python base image
FROM python:3.12-slim

# Python runtime settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Application directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root application user
RUN groupadd --system app && \
    useradd --system --gid app --create-home app

# Copy application source
COPY --chown=app:app . .

# Collect static files using temporary build-only settings
RUN DJANGO_SECRET_KEY=build-only-placeholder \
    VAULT_LOOKUP_SECRET=build-only-placeholder-012345678901234567890123456789 \
    USE_S3=False \
    python manage.py collectstatic --noinput

# Run as an unprivileged user
USER app

# Gunicorn listens on this port
EXPOSE 8000

# Application health check (TCP connection)
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import socket; s=socket.create_connection(('127.0.0.1', 8000), timeout=3); s.close()" || exit 1

# Start Django using Gunicorn
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--threads", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "filepad_project.wsgi:application"]
