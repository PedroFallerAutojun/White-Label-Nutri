# Backups para restauração local

Coloque aqui uma **cópia** do backup da instância (ex.: `BackupNutriJR`).
Esta pasta é montada no container do banco como **somente leitura** — o arquivo
original nunca é alterado (D-002).

Para restaurar na base local:

```bash
docker compose exec db dropdb -U postgres --if-exists nutri
docker compose exec db createdb -U postgres nutri
docker compose exec db pg_restore --no-owner --no-privileges -U postgres -d nutri /backups/BackupNutriJR
docker compose exec web python manage.py migrate --fake-initial
docker compose exec web python manage.py sanear_backup --dry-run   # relatório
docker compose exec web python manage.py sanear_backup             # aplica
```

Arquivos de backup não entram no controle de versão (ver .gitignore).
