FROM node:24-alpine AS frontend-builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
ENV NODE_ENV=production
COPY tsconfig.json vite.config.ts ./
COPY src ./src
RUN npm run build
# Ensure there are no type errors.
#RUN npx tsc --noEmit

FROM python:3.13-alpine
WORKDIR /app
EXPOSE 9090
ENV DEBUG=False
ENV DJANGO_VITE_DEV_MODE=False

COPY docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]

COPY requirements.txt manage.py ./
RUN apk add --no-cache libpq libc-dev linux-headers postgresql-dev \
    && pip install --no-cache-dir uwsgi psycopg2 \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del libc-dev linux-headers postgresql-dev

COPY habrasanta ./habrasanta
COPY --from=frontend-builder /app/dist ./dist

RUN python -m compileall habrasanta && \
    python manage.py collectstatic --no-input

CMD ["uwsgi", "--threads=20", "--uwsgi-socket=:9090", "--module=habrasanta.wsgi"]
