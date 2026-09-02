# White-Label-Nutri

Sistema de **fichas técnicas de preparações e tabelas nutricionais no padrão ANVISA**,
entregue como produto white-label: **uma instância por empresa**, cada cliente com banco
de dados e hospedagem próprios.

O que o sistema faz e para quem: [docs/VISAO_GERAL.md](docs/VISAO_GERAL.md).

## Stack
Django 5.2 LTS · PostgreSQL · Bootstrap 5 · pytest — detalhes em
[docs/ARQUITETURA.md](docs/ARQUITETURA.md).

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
destrói o banco de teste sozinho. Cobertura por camada em [docs/TESTES.md](docs/TESTES.md).

## Provisionar uma empresa nova
```bash
createdb nutri_acme
DATABASE_URL=postgres://.../nutri_acme python manage.py migrate
DATABASE_URL=postgres://.../nutri_acme python manage.py bootstrap_instancia \
    --nome "Nutri Acme" --admin ana --email ana@acme.com --chave ACME-2026
```

O deploy de cada empresa é independente: banco próprio, variáveis próprias. O `Procfile`
já traz o `migrate` de release e o gunicorn — passo a passo em
[docs/OPERACAO.md](docs/OPERACAO.md).

## Manutenção da base
```bash
python manage.py auditar_tabelas            # fichas com tabela defasada ou incoerente
python manage.py auditar_tabelas --limite 0 --detalhar
```

## Configuração
As variáveis de ambiente estão documentadas em `.env.example` e em
[docs/OPERACAO.md](docs/OPERACAO.md). Em produção, `SECRET_KEY` e `ALLOWED_HOSTS` são
obrigatórias — a aplicação falha no boot sem elas.

## Documentação
- [docs/VISAO_GERAL.md](docs/VISAO_GERAL.md) — o produto, o modelo white-label e o índice
- [docs/ARQUITETURA.md](docs/ARQUITETURA.md) — stack, estrutura do código, segurança, decisões
- [docs/REGRAS_DE_NEGOCIO.md](docs/REGRAS_DE_NEGOCIO.md) — BR-001..BR-030 (cálculo, rótulo, fichas)
- [docs/BANCO_DE_DADOS.md](docs/BANCO_DE_DADOS.md) — modelo de dados e invariantes
- [docs/INTERFACE.md](docs/INTERFACE.md) — as telas, com capturas
- [docs/OPERACAO.md](docs/OPERACAO.md) — provisionar, publicar, configurar e manter
- [docs/TESTES.md](docs/TESTES.md) — como rodar a suíte e o que ela cobre
