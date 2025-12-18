FROM python:3.10-alpine

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG=0

# Set work directory
WORKDIR /app

# Install system dependencies (if needed for your packages)
RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev

# Copy requirements first to leverage Docker cache
COPY ./requirements.txt .

# Upgrade pip and install all dependencies in one layer
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Install additional packages that might not be in requirements.txt
RUN pip install gunicorn python-dotenv

# Copy project
COPY . .

# Run migrations and start server
EXPOSE 8080
CMD python manage.py makemigrations && \
    python manage.py migrate && \
    gunicorn dict.wsgi:application --bind 0.0.0.0:$PORT