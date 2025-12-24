FROM python:3.9-alpine
WORKDIR /app
EXPOSE 9090
ENV DEBUG=False

RUN mkdir /data

COPY docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]

COPY requirements.txt manage.py ./
RUN apk add --no-cache libpq libc-dev linux-headers postgresql-dev \
    && pip install --no-cache-dir uwsgi psycopg2 \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del libc-dev linux-headers postgresql-dev

COPY habrasanta ./habrasanta
RUN python -m compileall habrasanta && \
    python manage.py collectstatic --no-input

CMD ["uwsgi", "--threads=20", "--uwsgi-socket=:9090", "--static-map=/backend/static=/app/staticfiles", "--module=habrasanta.wsgi"]
