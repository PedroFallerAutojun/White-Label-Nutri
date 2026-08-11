# White-Label-Nutri

Reimplementação do sistema **Nutri Jr** (fichas técnicas e tabelas nutricionais ANVISA)
como produto white-label: **uma instância por empresa**, cada cliente com banco de
dados e hospedagem próprios (ver `docs/DECISIONS.md`, D-009).

## Stack
Django 5.2 LTS · PostgreSQL · Bootstrap 5 · pytest — detalhes em `docs/NEW_ARCHITECTURE.md`.

## Rodando localmente (Windows, sem Docker)

Requisitos: **Python 3.12+** e **PostgreSQL 17+** (a versão 17 é necessária para
restaurar o `BackupNutriJR`). Instale com:

```powershell
winget install Python.Python.3.12
winget install PostgreSQL.PostgreSQL.17   # anote a senha do usuário "postgres"
```

Feche e reabra o terminal, então:

```powershell
Copy-Item ..\Nutri_Jr\BackupNutriJR backups\
.\scripts\preparar_local_sem_docker.ps1 backups\BackupNutriJR
```

O script cria o ambiente virtual, instala as dependências, restaura o backup numa
base local, roda o saneamento e sobe o servidor em <http://localhost:8000>.
Sem o argumento do backup, ele prepara uma instância nova e vazia.

### Já tenho PostgreSQL instalado

Descubra a versão e as instâncias em execução:

```powershell
Get-Service *postgres*          # nomes trazem a versão, ex.: postgresql-x64-16
psql --version
```

- **Versão 17 ou superior:** siga normalmente (informe a senha do usuário `postgres`).
- **Versão anterior à 17:** ela não restaura o `BackupNutriJR`. Instale a 17 ao lado —
  as duas convivem, e a nova normalmente fica na porta 5433:

  ```powershell
  winget install PostgreSQL.PostgreSQL.17
  .\scripts\preparar_local_sem_docker.ps1 backups\BackupNutriJR -Porta 5433
  ```

### Senha do PostgreSQL esquecida

O PostgreSQL não permite recuperar a senha, apenas trocá-la. Antes de trocar, vale
conferir se ela está salva em algum lugar:

```powershell
Get-Content "$env:APPDATA\postgresql\pgpass.conf"   # senhas salvas em texto puro, se existirem
```

Se não estiver, redefina com o script (abra o PowerShell **como Administrador**):

```powershell
.\scripts\redefinir_senha_postgres.ps1 -NovaSenha "minhaSenha123"
```

Ele localiza a instalação pelo serviço do Windows, libera a autenticação local por
alguns segundos, troca a senha e **restaura a configuração original** — inclusive se
algo falhar no meio (a restauração está num bloco `finally`). No fim, testa a nova
senha. Com mais de uma versão instalada, escolha qual com `-Versao 17`.

## Rodando com Docker (alternativa)

Requisitos: **Docker** e **Docker Compose v2** (`docker compose version` deve responder).

Primeira vez — clonar o repositório e entrar na branch:

```bash
git clone https://github.com/PedroFallerAutojun/White-Label-Nutri.git
cd White-Label-Nutri
git checkout claude/nutri-jr-reverse-engineering-kglfb4
```

**Instância nova, vazia** (cria administrador e chave de cadastro):

```bash
./scripts/preparar_local.sh          # Linux / macOS
.\scripts\preparar_local.ps1         # Windows (PowerShell)
```

**Com o acervo da Nutri Jr**, a partir de uma cópia do backup — o arquivo está
versionado no repositório do sistema original:

Linux / macOS:
```bash
git clone https://github.com/PedroFallerAutojun/Nutri_Jr.git ../Nutri_Jr
cp ../Nutri_Jr/BackupNutriJR backups/
./scripts/preparar_local.sh backups/BackupNutriJR
```

Windows (PowerShell):
```powershell
git clone https://github.com/PedroFallerAutojun/Nutri_Jr.git ..\Nutri_Jr
Copy-Item ..\Nutri_Jr\BackupNutriJR backups\
.\scripts\preparar_local.ps1 backups\BackupNutriJR
```
Se o PowerShell recusar a execução do script, libere para a sessão atual com
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

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
