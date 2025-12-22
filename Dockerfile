FROM python:3.10-alpine

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG=0

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    postgresql-dev \
    libffi-dev \
    openssl-dev

# Copy requirements first
COPY ./requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip install gunicorn python-dotenv psycopg2-binary

# Copy project
COPY . .

# Create a startup script
RUN echo '#!/bin/sh' > /app/start.sh && \
    echo 'echo "Waiting for database..."' >> /app/start.sh && \
    echo 'until nc -z $PGHOST $PGPORT; do' >> /app/start.sh && \
    echo '  echo "Database not ready - sleeping"' >> /app/start.sh && \
    echo '  sleep 2' >> /app/start.sh && \
    echo 'done' >> /app/start.sh && \
    echo 'echo "Database ready! Running migrations..."' >> /app/start.sh && \
    echo 'python manage.py makemigrations' >> /app/start.sh && \
    echo 'python manage.py migrate' >> /app/start.sh && \
    echo 'echo "Starting Gunicorn..."' >> /app/start.sh && \
    echo 'exec gunicorn dict.wsgi:application --bind 0.0.0.0:$PORT' >> /app/start.sh && \
    chmod +x /app/start.sh

EXPOSE 8080
CMD ["/app/start.sh"]