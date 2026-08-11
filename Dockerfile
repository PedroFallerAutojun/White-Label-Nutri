# Imagem da aplicação — a mesma para todas as instâncias (empresas clientes).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# libpq é necessária para o psycopg; o restante é limpo na mesma camada.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt ./
ARG INSTALAR_DEV=false
RUN if [ "$INSTALAR_DEV" = "true" ]; then \
        pip install -r requirements-dev.txt; \
    else \
        pip install -r requirements.txt; \
    fi

COPY . .

# Usuário sem privilégios (o processo não precisa de root).
RUN useradd --create-home --uid 1000 nutri \
    && mkdir -p /app/staticfiles /app/media \
    && chown -R nutri:nutri /app
USER nutri

EXPOSE 8000
ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi", "--bind", "0.0.0.0:8000", "--workers", "3", "--log-file", "-"]
