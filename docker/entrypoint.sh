#!/bin/sh
# Prepara a instância antes de iniciar o processo principal.
set -e

echo "[entrypoint] aguardando o banco de dados..."
python - <<'PY'
import os, time
import psycopg
url = os.environ["DATABASE_URL"]
for tentativa in range(60):
    try:
        with psycopg.connect(url, connect_timeout=3):
            break
    except Exception as erro:
        if tentativa == 59:
            raise SystemExit(f"banco indisponível: {erro}")
        time.sleep(1)
PY

# --fake-initial serve aos dois cenários: banco vazio (aplica tudo) e banco
# restaurado do backup legado (reconhece o schema existente — D-003).
echo "[entrypoint] aplicando migrations..."
python manage.py migrate --fake-initial --noinput

if [ "${COLETAR_ESTATICOS:-true}" = "true" ]; then
  echo "[entrypoint] coletando arquivos estáticos..."
  python manage.py collectstatic --noinput --clear >/dev/null
fi

echo "[entrypoint] iniciando: $*"
exec "$@"
