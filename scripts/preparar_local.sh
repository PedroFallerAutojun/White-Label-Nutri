#!/usr/bin/env bash
# Prepara o ambiente local com Docker: sobe os serviços e configura a instância.
#
#   ./scripts/preparar_local.sh                        # instância nova (vazia)
#   ./scripts/preparar_local.sh backups/BackupNutriJR  # restaura o acervo legado
#
# O arquivo de backup precisa estar dentro da pasta backups/ (montada como
# somente leitura no container do banco — D-002).
set -euo pipefail

cd "$(dirname "$0")/.."

BACKUP="${1:-}"
USUARIO_DB="${POSTGRES_USER:-postgres}"
BANCO="${POSTGRES_DB:-nutri}"

if ! docker compose version >/dev/null 2>&1; then
  echo "erro: 'docker compose' não está disponível. Instale o Docker Compose v2." >&2
  exit 1
fi

if [ -n "$BACKUP" ] && [ ! -f "$BACKUP" ]; then
  echo "erro: arquivo '$BACKUP' não encontrado." >&2
  echo "Copie o backup para a pasta backups/ e informe o caminho, por exemplo:" >&2
  echo "  cp ../Nutri_Jr/BackupNutriJR backups/ && $0 backups/BackupNutriJR" >&2
  exit 1
fi

aguardar_banco() {
  echo "==> aguardando o banco"
  for _ in $(seq 60); do
    if docker compose exec -T db pg_isready -U "$USUARIO_DB" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  echo "erro: o banco não ficou disponível." >&2
  exit 1
}

if [ -n "$BACKUP" ]; then
  # A restauração recria o banco, então a aplicação fica fora do ar durante o
  # processo: com o serviço web conectado, o dropdb falharia.
  echo "==> subindo apenas o banco (a aplicação sobe depois da restauração)"
  docker compose up -d --build db
  aguardar_banco

  ARQUIVO="/backups/$(basename "$BACKUP")"
  echo "==> restaurando $ARQUIVO (o arquivo original não é alterado)"
  docker compose exec -T db dropdb -U "$USUARIO_DB" --if-exists --force "$BANCO"
  docker compose exec -T db createdb -U "$USUARIO_DB" "$BANCO"
  docker compose exec -T db pg_restore --no-owner --no-privileges \
    -U "$USUARIO_DB" -d "$BANCO" "$ARQUIVO"

  # O entrypoint do web aplica migrate --fake-initial ao iniciar, reconhecendo
  # o schema legado sem recriá-lo.
  echo "==> subindo a aplicação"
  docker compose up -d --build web

  echo "==> saneamento (relatório, nada é gravado)"
  docker compose exec -T web python manage.py sanear_backup --dry-run
  echo "==> saneamento (aplicando)"
  docker compose exec -T web python manage.py sanear_backup

  echo
  echo "Acervo restaurado. Entre com um usuário existente da instância."
  echo "Para criar um acesso local, rode:"
  echo "  docker compose exec web python manage.py createsuperuser"
else
  echo "==> subindo os serviços"
  docker compose up -d --build
  aguardar_banco
  # O entrypoint já roda as migrations; aqui só configuramos a instância.
  docker compose exec -T \
    -e INSTANCIA_ADMIN_SENHA="${INSTANCIA_ADMIN_SENHA:-admin-local-123456}" web \
    python manage.py bootstrap_instancia \
      --nome "${NOME_INSTANCIA:-Nutri Local}" \
      --admin "${ADMIN_INSTANCIA:-admin}" \
      --chave "${CHAVE_CADASTRO:-CHAVE-LOCAL}" \
    || echo "(instância já estava configurada — nada a fazer)"

  echo
  echo "Instância nova pronta."
  echo "  usuário: ${ADMIN_INSTANCIA:-admin}"
  echo "  senha:   ${INSTANCIA_ADMIN_SENHA:-admin-local-123456}"
  echo "  chave de cadastro: ${CHAVE_CADASTRO:-CHAVE-LOCAL}"
fi

echo "Aplicação: http://localhost:${PORTA_WEB:-8000}"
