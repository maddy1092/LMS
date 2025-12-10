#!/bin/bash
set -e

echo "Starting deployment..."

# Create migrations for all apps
echo "Creating migrations..."
python manage.py makemigrations --noinput

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the application
echo "Starting Gunicorn..."
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120
