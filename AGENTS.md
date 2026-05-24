# Agent Instructions

This is the source code of https://habra-adm.ru, both the backend and frontend (Preact, TypeScript).

Habra-ADM (spelled "Хабра-АДМ" in Russian) is a website which allows the users of Habr (https://habr.com) to share christmas gifts anonymously (Secret Santa).

The website runs in a Docker container in production, using PostgreSQL as the database and Redis for in-memory cache.

If something about the architecture is unclear, better ask than guess. Always ask if you believe an action you're trying to perform is dangerous.

If you believe there is a mistake in these instructions, e.g. they are outdated and do not match the project anymore, tell the user.

## Backend

The backend code is in the `habrasanta/` directory. It is a single-app Django project. Both the configuration (e.g. `wsgi.py`, `settings.py`) and the app (e.g. `views.py`, `models.py`) are in the same directory for simplicity.

Always work in the virtual environment from the `venv/` directory. Never try installing something globally.

The project has some unit tests which you can run via `venv/bin/python manage.py test`. Sometimes it is better to adjust the tests instead of trying to replicate the old behavior. In this case, stop and ask the user.

The source code must pass strict MyPy validation. Use `venv/bin/mypy habrasanta/` to check.

The project uses Ruff as the linter and formatter. Use `venv/bin/ruff check habrasanta/` and `venv/bin/ruff format --check habrasanta/` to check.

## Frontend

The frontend code is in the `src/` directory. It uses Preact and is written in TypeScript, the build system is Vite.
