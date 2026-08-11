#!/usr/bin/env bash
# Prepara o ambiente local com Docker: sobe os serviços e configura a instância.
#
#   ./scripts/preparar_local.sh                      # instância nova (vazia)
#   ./scripts/preparar_local.sh backups/BackupNutriJR # restaura o acervo legado
set -euo pipefail

BACKUP="${1:-}"
USUARIO_DB="${POSTGRES_USER:-postgres}"
BANCO="${POSTGRES_DB:-nutri}"

echo "==> subindo os serviços"
docker compose up -d --build

echo "==> aguardando o banco"
until docker compose exec -T db pg_isready -U "$USUARIO_DB" -d "$BANCO" >/dev/null 2>&1; do
  sleep 1
done

if [ -n "$BACKUP" ]; then
  ARQUIVO="/backups/$(basename "$BACKUP")"
  echo "==> restaurando $ARQUIVO (o arquivo original não é alterado)"
  docker compose exec -T db dropdb -U "$USUARIO_DB" --if-exists "$BANCO"
  docker compose exec -T db createdb -U "$USUARIO_DB" "$BANCO"
  docker compose exec -T db pg_restore --no-owner --no-privileges \
    -U "$USUARIO_DB" -d "$BANCO" "$ARQUIVO"

  echo "==> reconhecendo o schema legado"
  docker compose exec -T web python manage.py migrate --fake-initial --noinput

  echo "==> saneamento (relatório)"
  docker compose exec -T web python manage.py sanear_backup --dry-run
  echo "==> saneamento (aplicando)"
  docker compose exec -T web python manage.py sanear_backup
else
  echo "==> configurando uma instância nova"
  docker compose exec -T web python manage.py migrate --noinput
  docker compose exec -T -e INSTANCIA_ADMIN_SENHA="${INSTANCIA_ADMIN_SENHA:-admin-local-123456}" web \
    python manage.py bootstrap_instancia \
      --nome "${NOME_INSTANCIA:-Nutri Local}" \
      --admin "${ADMIN_INSTANCIA:-admin}" \
      --chave "${CHAVE_CADASTRO:-CHAVE-LOCAL}" \
    || echo "(instância já estava configurada — nada a fazer)"
fi

echo
echo "Pronto: http://localhost:${PORTA_WEB:-8000}"
