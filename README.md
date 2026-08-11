# White-Label-Nutri

Reimplementação do sistema **Nutri Jr** (fichas técnicas e tabelas nutricionais ANVISA)
como produto white-label: **uma instância por empresa**, cada cliente com banco de
dados e hospedagem próprios (ver `docs/DECISIONS.md`, D-009).

## Stack
Django 5.2 LTS · PostgreSQL · Bootstrap 5 · pytest — detalhes em `docs/NEW_ARCHITECTURE.md`.

## Rodando com Docker (caminho mais curto)

Requisitos: **Docker** e **Docker Compose v2** (`docker compose version` deve responder).

Primeira vez — clonar o repositório e entrar na branch:

```bash
git clone https://github.com/PedroFallerAutojun/White-Label-Nutri.git
cd White-Label-Nutri
git checkout claude/nutri-jr-reverse-engineering-kglfb4
```

**Instância nova, vazia** (cria administrador e chave de cadastro):

```bash
./scripts/preparar_local.sh
```

**Com o acervo da Nutri Jr**, a partir de uma cópia do backup — o arquivo está
versionado no repositório do sistema original:

```bash
git clone https://github.com/PedroFallerAutojun/Nutri_Jr.git ../Nutri_Jr
cp ../Nutri_Jr/BackupNutriJR backups/
./scripts/preparar_local.sh backups/BackupNutriJR
```

Depois: <http://localhost:8000>. A primeira execução baixa as imagens e instala as
dependências (alguns minutos); as seguintes são rápidas.

Numa instância nova, o script cria o administrador `admin` com senha
`admin-local-123456` e a chave de cadastro `CHAVE-LOCAL` (personalizáveis por
variáveis de ambiente — veja o script). Ao restaurar o acervo legado, os usuários
são os reais do backup; para criar um acesso local use
`docker compose exec web python manage.py createsuperuser`.

Se a porta 8000 ou 5433 estiver ocupada: `PORTA_WEB=8080 PORTA_DB=5544 ./scripts/preparar_local.sh`.

O PostgreSQL do compose é a **versão 17** de propósito: o `BackupNutriJR` foi gerado
com pg_dump 17 e só é restaurável por um pg_restore 17+. A pasta `backups/` é montada
como **somente leitura**, então o arquivo original nunca é alterado.

Comandos úteis:
```bash
docker compose logs -f web
docker compose exec web pytest -q
docker compose exec web python manage.py sanear_backup --dry-run
docker compose down            # para tudo (mantém o banco)
docker compose down -v         # apaga também o volume do banco
```

## Desenvolvimento (sem Docker)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL=postgres://user:pass@localhost:5432/nutri
python manage.py migrate            # instância nova
# ou, sobre um banco restaurado do backup legado:
python manage.py migrate --fake-initial
python manage.py runserver
pytest

# paridade ponta a ponta contra o acervo legado restaurado
PARIDADE_DB=nutri_paridade pytest tests/integration/test_paridade_rotulo_e2e.py
```

## Provisionar uma empresa nova
```bash
createdb nutri_acme
DATABASE_URL=postgres://.../nutri_acme python manage.py migrate
DATABASE_URL=postgres://.../nutri_acme python manage.py bootstrap_instancia \
    --nome "Nutri Acme" --admin ana --email ana@acme.com --chave ACME-2026
```

## Migrar a instância Nutri Jr
Restaure uma cópia do `BackupNutriJR` (PostgreSQL 17+), então:
```bash
python manage.py migrate --fake-initial
python manage.py sanear_backup --dry-run   # relatório
python manage.py sanear_backup             # aplica
```
Detalhes em `docs/MIGRATION.md`.

## Status
Etapas concluídas: E1 (fundação), E2 (cálculo e rótulo com paridade validada),
E3/E4 (telas do wizard, ingredientes, upload e rótulo final), E5 (membros e
administração), E6 (saneamento e provisionamento de instâncias).

E7 (segurança, performance e documentação de paridade) concluída.

Paridade com o sistema original: **1.557/1.557 rótulos idênticos**; após o
saneamento, **as 1.574 fichas do acervo abrem sem erro** (17 davam 500 no original).
Suíte: **117 testes**. Detalhes em `docs/PARITY_MATRIX.md`.

## Configuração
As variáveis de ambiente estão documentadas em `.env.example`. Em produção,
`SECRET_KEY` e `ALLOWED_HOSTS` são obrigatórias — a aplicação falha no boot sem elas.

## Documentação
- `docs/REVERSE_ENGINEERING.md` — engenharia reversa do sistema original
- `docs/BUSINESS_RULES.md` — regras de negócio (BR-001..BR-030)
- `docs/NEW_ARCHITECTURE.md` — arquitetura da nova versão e fases E1–E7
- `docs/MIGRATION.md` — restauração do backup e saneamento
- `docs/TESTING.md` — estratégia de paridade (golden dataset em `tests/golden/`)
- `docs/PARITY_MATRIX.md` — matriz de paridade Original × Novo
- `docs/DECISIONS.md` — registro de decisões
