# Secret Santa - Habr.com edition

https://habra-adm.ru was founded in 2012 by @negasus and @kafeman who were inspired by a similar project on Dirty.

In 2013 Habr decided to collaborate by introducing OAuth support on their side and making advertisements on the website.
[Valery Novosylov](https://novosylov.livejournal.com) created a wonderful web design.

In 2015 tan4ikweb created a wonderful web design for a spinoff version on Geektimes (not available anymore).
The source code was uploaded to GitHub.

In 2023 Boomburum joined the organization team and @Inzeppelin upgraded the frontend.
Habr lawyers also helped writing [terms of use](https://habra-adm.ru/terms) and a [privacy policy](https://habra-adm.ru/privacy) for the project.

## Testing without installation

Visit https://beta.habrasanta.org or join other Secret Santas on https://habra-adm.ru.

## Running locally

```bash
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
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

Use Docker image `ghcr.io/habrasanta/backend`, tag `main` for the staging environment, `v*` for production.
Skipping versions between updates should be avoided (an older container may crash while accessing a newer DB schema).
Running two successive versions simultaneously is supported (e.g. `v1.0.0` and `v1.0.1`).

Default command starts an HTTP server (gunicorn) on port 8080 (or whatever value the `PORT` variable is set to, see below).
The maximum number of such HTTP containers running simultaneously is not limited.
A very simple health check endpoint is available at `GET /backend/health`.

To send out notifications, run a worker container using the command
`celery -A habrasanta worker -P solo -l INFO` (check out [this](https://docs.celeryq.dev/en/stable/reference/cli.html) to learn more).
A single worker container is necessary and sufficient.
Nothing bad should happen if there is more than one worker container running simultaneously (e.g. during deployment of a newer version).

Run a cron container using the command `crond -f`.
Avoid running more than one cron containers at the same time.
During updates, stop the old container before starting a new one.
Nothing bad happens if the cron container is down for some time (up to several hours).

For all containers, set the following environment variables:

| Name| Value |
| ------------- | ------------- |
| `DEBUG` | `True` on staging, `False` in production. |
| `SECRET_KEY` | Any random string to sign cookies and tokens. Use something like `openssl rand -base64 32` to generate. |
| `DB_ENGINE` | Which DB adapter to use, e.g. `django.db.backends.postgresql` for PostgreSQL or `django.db.backends.mysql` for MySQL/MardiDB. Check out [this](https://docs.djangoproject.com/en/6.0/ref/databases/) and [this](https://docs.djangoproject.com/en/6.0/ref/settings/#databases) to learn more. |
| `DB_NAME` | DB name. |
| `DB_USER` | Username to connect to the DB. |
| `DB_PASS` | Password to connect to the DB. |
| `DB_HOST` | IP address or hostname of the DB. |
| `CACHE_BACKEND` | Which cache adapter to use, e.g. `django.core.cache.backends.redis.RedisCache`. Check out [this](https://docs.djangoproject.com/en/6.0/topics/cache/) and [this](https://docs.djangoproject.com/en/6.0/ref/settings/#std-setting-CACHES-BACKEND) to learn more. |
| `CACHE_LOCATION` | Where to find the cache backend, e.g. `redis://localhost`. |
| `CELERY_BROKER_URL` | Where to find redis? E.g. `redis://redis.example.com/1` |
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

Beware that the app expects the user IP address being in the `X-Real-IP` header.
It is also a good idea to enable caching at the frontend level (e.g. Nginx), especially for the `/static/` routes.
The backend is expected to always return correct `Cache-Control` and `Vary` headers indicating which requests may be cached.
