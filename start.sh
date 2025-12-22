#!/bin/sh

echo "Starting Django application..."

# Extract database info from DATABASE_URL if it exists
if [ -n "$DATABASE_URL" ]; then
    echo "DATABASE_URL found, parsing connection details..."
    # Parse DATABASE_URL (postgresql://user:pass@host:port/dbname)
    DB_HOST_PORT=$(echo $DATABASE_URL | sed -e 's/.*@//' -e 's/\/.*//')
    DB_HOST=$(echo $DB_HOST_PORT | cut -d: -f1)
    DB_PORT=$(echo $DB_HOST_PORT | cut -d: -f2)
    
    if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
        echo "Waiting for database at $DB_HOST:$DB_PORT..."
        timeout=30
        while ! nc -z $DB_HOST $DB_PORT; do
            echo "Database not ready - sleeping"
            sleep 2
            timeout=$((timeout-2))
            if [ $timeout -le 0 ]; then
                echo "Database connection timeout!"
                break
            fi
        done
        echo "Database is ready!"
    fi
fi

# Run migrations
echo "Running database migrations..."
python manage.py makemigrations --noinput || echo "Makemigrations failed, continuing..."
python manage.py migrate --noinput || echo "Migrate failed, continuing..."

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "Collectstatic failed, continuing..."

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn dict.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -