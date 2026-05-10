FROM node:24-alpine AS frontend-builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY tsconfig.json vite.config.ts ./
COPY src ./src
RUN npm run build
# Ensure there are no type errors.
#RUN npx tsc --noEmit

FROM python:3.13-alpine
WORKDIR /app
EXPOSE 8080
ENV DEBUG=False
ENV PORT=8080

COPY docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]

COPY requirements.txt manage.py ./
RUN apk add --no-cache libpq postgresql-dev \
    && pip install --no-cache-dir gunicorn psycopg2 \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del postgresql-dev

COPY habrasanta ./habrasanta
COPY --from=frontend-builder /app/dist ./dist

RUN python -m compileall habrasanta && \
    python manage.py collectstatic --no-input

# Set after "python manage.py collectstatic", otherwise there is a warning:
# Cannot read Vite manifest file for app default at /app/staticfiles/manifest.json :
#     [Errno 2] No such file or directory: '/app/staticfiles/manifest.json'
ENV DJANGO_VITE_DEV_MODE=False

CMD ["gunicorn", "--workers", "10", "habrasanta.wsgi"]
