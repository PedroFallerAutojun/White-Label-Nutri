# White-Label-Nutri

Reimplementação do sistema **Nutri Jr** (fichas técnicas e tabelas nutricionais ANVISA)
como produto white-label: **uma instância por empresa**, cada cliente com banco de
dados e hospedagem próprios (ver `docs/DECISIONS.md`, D-009).

## Stack
Django 5.2 LTS · PostgreSQL · Bootstrap 5 · pytest — detalhes em `docs/NEW_ARCHITECTURE.md`.

## Rodando localmente

Requisitos: **Python 3.12+** e **PostgreSQL 14+**.

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt

createdb nutri                                      # banco local desta instância
export DATABASE_URL=postgres://postgres:senha@localhost:5432/nutri
python manage.py migrate
python manage.py bootstrap_instancia --nome "Nutri Local" \
    --admin admin --email admin@exemplo.com --chave CHAVE-LOCAL
python manage.py runserver
```

A aplicação sobe em <http://localhost:8000>; entre com o usuário criado pelo
`bootstrap_instancia`. As variáveis de ambiente podem ficar num arquivo `.env` na
raiz (modelo em `.env.example`) em vez de exportadas na sessão.

Para popular a base de ingredientes, use a tela **Ingredientes → Importar TXT** com
um arquivo da TACO (TXT separado por TAB), ou cadastre um a um.

## Testes
```bash
pytest -q
```
Precisam de um PostgreSQL acessível pela `DATABASE_URL` — o pytest-django cria e
destrói o banco de teste sozinho. Estratégia e cobertura em `docs/TESTING.md`.

## Provisionar uma empresa nova
```bash
createdb nutri_acme
DATABASE_URL=postgres://.../nutri_acme python manage.py migrate
DATABASE_URL=postgres://.../nutri_acme python manage.py bootstrap_instancia \
    --nome "Nutri Acme" --admin ana --email ana@acme.com --chave ACME-2026
```

O deploy de cada empresa é independente (D-009): banco próprio, variáveis próprias.
O `Procfile` já traz o `migrate` de release e o gunicorn.

## Manutenção da base
```bash
python manage.py auditar_tabelas            # fichas com tabela defasada ou incoerente
python manage.py auditar_tabelas --limite 20
```

## Status
Etapas concluídas: E1 (fundação), E2 (cálculo e rótulo com paridade validada),
E3/E4 (telas do wizard, ingredientes, upload e rótulo final), E5 (membros e
administração), E6 (provisionamento de instâncias).

E7 (segurança, performance e documentação de paridade) concluída.

Paridade com o sistema original: **1.557/1.557 rótulos idênticos**; após o
saneamento, **as 1.574 fichas do acervo abrem sem erro** (17 davam 500 no original).
Suíte: **117 testes**. Detalhes em `docs/PARITY_MATRIX.md`.

## Configuração
As variáveis de ambiente estão documentadas em `.env.example`. Em produção,
`SECRET_KEY` e `ALLOWED_HOSTS` são obrigatórias — a aplicação falha no boot sem elas.

## Identidade visual da empresa (white-label)

Nome, cor e logotipo ficam em **Configuração da instância**, no Django admin
(`/admin/`). O logotipo é guardado **no banco desta instância** — não em arquivo —
porque plataformas de disco efêmero apagariam o upload no próximo restart.

Aceita PNG, JPG ou WEBP até 1 MB, validados pelo conteúdo do arquivo. Aparece na
tela de login e no topo do sistema. Para trocar, basta enviar outro; a marca antiga
some do cache do navegador na hora.

## Documentação
- `docs/REVERSE_ENGINEERING.md` — engenharia reversa do sistema original
- `docs/BUSINESS_RULES.md` — regras de negócio (BR-001..BR-030)
- `docs/NEW_ARCHITECTURE.md` — arquitetura da nova versão e fases E1–E7
- `docs/MIGRATION.md` — restauração do backup e saneamento
- `docs/TESTING.md` — estratégia de paridade (golden dataset em `tests/golden/`)
- `docs/BACKLOG_ETAPA1.md` — conformidade com o backlog da Etapa 1 (requisitos do cliente)
- `docs/PARITY_MATRIX.md` — matriz de paridade Original × Novo
- `docs/DECISIONS.md` — registro de decisões
