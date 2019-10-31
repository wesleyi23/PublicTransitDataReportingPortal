#!/bin/sh

#python manage.py migrate
python manage.py collectstatic --no-input --clear
gunicorn -b 0.0.0.0:8000 TransitData.wsgi:application
exec "$@"