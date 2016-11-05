set -e

./setupConfig.sh
python manage.py makemigrations transcroobie
python manage.py migrate --fake-initial

redis-server &
celery -A transcroobie worker --loglevel=info &

python manage.py runserver 0.0.0.0:$PORT
