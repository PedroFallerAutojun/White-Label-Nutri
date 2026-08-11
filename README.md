# White-Label-Nutri

Reimplementação do sistema **Nutri Jr** (fichas técnicas e tabelas nutricionais ANVISA)
como produto white-label: **uma instância por empresa**, cada cliente com banco de
dados e hospedagem próprios (ver `docs/DECISIONS.md`, D-009).

## Stack
Django 5.2 LTS · PostgreSQL · Bootstrap 5 · pytest — detalhes em `docs/NEW_ARCHITECTURE.md`.

## Desenvolvimento
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
