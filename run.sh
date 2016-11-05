set -e

./setupConfig.sh
python manage.py makemigrations transcroobie
python manage.py migrate --fake-initial

if [[ $IS_DEV_ENV=="0" ]]; then
    # Not needed on heroku server
    redis-server &
fi
celery -A transcroobie worker --loglevel=info &

python manage.py runserver 0.0.0.0:$PORT
