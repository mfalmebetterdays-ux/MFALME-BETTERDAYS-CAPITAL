FROM python:3.10-alpine

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    postgresql-dev \
    gcc \
    python3-dev \
    musl-dev \
    libffi-dev \
    openssl-dev \
    netcat-openbsd

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . .

# Make start script executable
RUN chmod +x /app/start.sh

# Expose port
EXPOSE $PORT

# Start the application
CMD ["/app/start.sh"]