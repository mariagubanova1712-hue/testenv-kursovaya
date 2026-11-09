FROM postgres:16-alpine
# скрипты из этой папки postgres выполняет при первой инициализации базы
COPY --chmod=644 init.sql /docker-entrypoint-initdb.d/01-init.sql
HEALTHCHECK --interval=5s --timeout=3s --retries=10 \
  CMD pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" || exit 1
