FROM python:3.10-alpine

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBUG 0

# Set work directory
WORKDIR /app

# Install dependencies
COPY ./requirements.txt .
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install gunicorn
RUN pip install Pillow

# Copy project
COPY . .
RUN pip install -r requirements.txt

# Run collectstatic during build
RUN python manage.py collectstatic --noinput

EXPOSE 8080

# ✅ CORRECT: Only start gunicorn, NO migrations here!
CMD gunicorn dict.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120