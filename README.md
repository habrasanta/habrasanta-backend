# Habrasanta backend

## Testing without installation

Visit https://beta.habrasanta.org

## Running locally

```bash
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ docker run --rm -p 6379:6379 redis:alpine
$ python manage.py migrate
$ python manage.py runserver
```

To match addresses or schedule chat notifications:

```bash
$ python manage.py cron
```

To send out notifications:

```bash
$ celery -A habrasanta worker -P solo -l INFO
```

To make sure it still works:

```bash
$ python manage.py test
```
