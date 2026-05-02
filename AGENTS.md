# Agent Instructions

This is the source code of https://habra-adm.ru, both the backend and frontend (Preact, TypeScript).

Habra-ADM (spelled "Хабра-АДМ" in Russian) is a website which allows the users of Habr (https://habr.com) to share christmas gifts anonymously (Secret Santa).

The website runs in a Docker container in production, using PostgreSQL as the database and Redis for in-memory cache.

If something about the architecture is unclear, better ask than guess. Always ask if you believe an action you're trying to perform is dangerous.

## Backend

The backend code is in the `habrasanta/` directory. A Django project and a Django app are both combined in the same directory for simplicity.

Always work in a virtual environment from the `venv/` directory. Never try installing something globally.

To run the tests, you need a Redis instance. Start it by using `podman run -d --rm -p 127.0.0.1:6379:6379 docker.io/library/redis:8-alpine`. Stop it when you finished testing.

## Frontend

The frontend code is in the `src/` directory. It uses Preact and is written in TypeScript, the build system is WebPack.
