#!/usr/bin/env bash
set -e

python -m pip install --upgrade pip
pip install -r requirements.txt

# collect static files
python manage.py collectstatic --noinput

# run migrations (optional - see note below)
python manage.py migrate --noinput || true
