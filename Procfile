release: python manage.py migrate --no-input
web: python check_db.py && gunicorn dict.wsgi:application --bind 0.0.0.0:$PORT