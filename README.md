# Secret Santa - Habr.com edition

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

## Production deployment

Use Docker image `ghcr.io/habrasanta/backend`,
tag `latest` for the staging environment, `v*` for production.

Default command starts an HTTP server on port 8080.

To send out notifications, run a worker container using the command
`celery -A habrasanta worker -P solo -l INFO`.

For all containers, set the following environment variables:

| Name| Value |
| ------------- | ------------- |
| `DEBUG` | `True` on staging, `False` in production. |
| `SECRET_KEY` | Any random string. |
| `DB_ENGINE` | `django.db.backends.postgresql` |
| `DB_NAME` | DB name. |
| `DB_USER` | Username to connect to the DB. |
| `DB_PASS` | Password to connect to the DB. |
| `DB_HOST` | IP address or hostname of the DB. |
| `REDIS_URL` | Where to find redis? E.g. `redis://redis.example.com/1` |
| `HABR_CLIENT_ID` | Client ID for access to the Habr API. |
| `HABR_CLIENT_SECRET` | Client secret for access to the Habr API. |
| `HABR_APIKEY` | API key for access to the Habr API. |
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | IP address or hostname of the SMTP server. |
| `EMAIL_PORT` | Port number to connect to the SMTP server. |
| `EMAIL_HOST_USER` | Username to connect to the SMTP server. |
| `EMAIL_HOST_PASSWORD` | Password to connect to the SMTP server. |
| `AUTHENTICATION_BACKEND` | `habrasanta.auth.PublicHabrBackend` in production, do not set on staging (defaults to `habrasanta.auth.FakeBackend`). |

For the container running gunicorn you might also want to adjust the following variables:

| Name | Description | Default |
| ---- | ----------- | ------- |
| `PORT` | TCP port to listen on. | `8080` |
| `FORWARDED_ALLOW_IPS` | List of IP addresses or CIDR networks from which some `X-Forwarded-` headers are accepted. See [here](https://gunicorn.org/reference/settings/#forwarded_allow_ips) for more details. | `127.0.0.1,::1` |
