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
```

## Documentação
- `docs/REVERSE_ENGINEERING.md` — engenharia reversa do sistema original
- `docs/BUSINESS_RULES.md` — regras de negócio (BR-001..BR-030)
- `docs/NEW_ARCHITECTURE.md` — arquitetura da nova versão e fases E1–E7
- `docs/MIGRATION.md` — restauração do backup e saneamento
- `docs/TESTING.md` — estratégia de paridade (golden dataset em `tests/golden/`)
- `docs/DECISIONS.md` — registro de decisões
