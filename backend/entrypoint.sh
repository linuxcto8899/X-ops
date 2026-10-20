#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Daphne server..."
exec daphne -b 0.0.0.0 -p 8000 ops_platform.asgi:application
