release: python manage.py makemigrations
release: python manage.py migrate
web: daphne pandemic_back.asgi:application --port $PORT --bind 0.0.0.0 -v2
