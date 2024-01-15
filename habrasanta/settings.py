import os

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "insecure default")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "yes", "on", "1")

ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = ["http://localhost:9000"]

INSTALLED_APPS = [
    "habrasanta",
    "django_countries",
    "django_celery_results",
    "drf_spectacular",
    "rest_framework",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "habrasanta.middleware.LastOnlineMiddleware",
]

ROOT_URLCONF = "habrasanta.urls"
WSGI_APPLICATION = "habrasanta.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://localhost"),
    }
}

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DB_NAME", BASE_DIR / "db.sqlite3"),
        "USER": os.getenv("DB_USER", ""),
        "PASSWORD": os.getenv("DB_PASS", ""),
        "HOST": os.getenv("DB_HOST", ""),
        "PORT": os.getenv("DB_PORT", ""),
        "CONN_MAX_AGE": 900,
        "CONN_HEALTH_CHECKS": True,
        "ATOMIC_REQUESTS": True,
    },
}

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 20,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Хабра АДМ",
    "DESCRIPTION": "API Клуба анонимных Дедов Морозов на Хабре. Внешний доступ не предусмотрен. Документация предназначена для желающих поработать над нашим frontend.",
    "VERSION": "1.0.0",
    "SCHEMA_PATH_PREFIX": "/api/v[0-9]",
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "with_time": {
            "format": "%(asctime)s\t%(levelname)s\t%(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "with_time",
        }
    },
    "loggers": {
        "urllib3": {
            "level": "DEBUG",
            "handlers": ["console"],
        },
    }
}

# Send debugging information to kafeman when the site crashes.
ADMINS = [
    ("kafeman", "kafemanw@gmail.com"),
]
SERVER_EMAIL = "django@mailgun.habrasanta.org"

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "backend/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

LOGIN_URL = "login"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = "habrasanta.User"
AUTHENTICATION_BACKENDS = [os.getenv("AUTHENTICATION_BACKEND", "habrasanta.auth.FakeBackend")]

HABR_CLIENT_ID = os.getenv("HABR_CLIENT_ID", "")
HABR_CLIENT_SECRET = os.getenv("HABR_CLIENT_SECRET", "")
HABR_APIKEY = os.getenv("HABR_APIKEY", "")
HABR_LOGIN_URL = "https://habr.com/auth/o/login/"
HABR_TOKEN_URL = "https://habr.com/auth/o/access-token/"
HABR_USER_INFO_URL = "https://habr.com/api/v2/me"
HABR_USER_AGENT = os.getenv("HABR_USER_AGENT", "Habrasanta/1.0 (open source)")

DEFAULT_FROM_EMAIL = "Хабра-АДМ <noreply@mailgun.habrasanta.org>"
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = True
EMAIL_TIMEOUT = 60

CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost")
CELERY_RESULT_BACKEND = "django-db"
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = False

HABRASANTA_ADMINS = os.getenv("HABRASANTA_ADMINS", "kafeman,negasus").split(",")
HABRASANTA_KARMA_LIMIT = 7.0
