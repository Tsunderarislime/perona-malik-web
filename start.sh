#!/usr/bin/env bash
# Start celery workers
celery -A app.celery worker --loglevel=INFO &
celery -A app.celery beat --loglevel=INFO &

# Start gunicorn
gunicorn --bind 0.0.0.0:8000 app:app