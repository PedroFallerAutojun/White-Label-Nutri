# Prepara o ambiente local no Windows SEM Docker (PowerShell).
#
#   .\scripts\preparar_local_sem_docker.ps1                        # instancia nova
#   .\scripts\preparar_local_sem_docker.ps1 backups\BackupNutriJR  # com o acervo
#
# Requisitos: Python 3.12+ e PostgreSQL 17+ instalados.
# O script verifica os dois e explica como instalar o que faltar.

param(
    [string]$Backup = "",
    [string]$Banco = "nutri",
    [string]$UsuarioDb = "postgres",
    # Porta do PostgreSQL. Se voce instalou a versao 17 ao lado de uma anterior,
    # a nova normalmente fica em 5433 (veja: Get-Service *postgres*).
    [int]$Porta = 5432
)

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

function Achar-Python {
    foreach ($candidato in @("py", "python", "python3")) {
        $caminho = Get-Command $candidato -ErrorAction SilentlyContinue
        if (-not $caminho) { continue }
        $versao = & $candidato -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
        if ($LASTEXITCODE -eq 0 -and [version]$versao -ge [version]"3.12") {
            return $candidato
        }
    }
    return $null
}

function Achar-Pasta-Postgres {
    # Primeiro no PATH; depois nas pastas padrao de instalacao do Windows.
    if (Get-Command pg_restore -ErrorAction SilentlyContinue) { return "" }
    $bases = @("$env:ProgramFiles\PostgreSQL", "${env:ProgramFiles(x86)}\PostgreSQL")
    foreach ($base in $bases) {
        if (-not (Test-Path $base)) { continue }
        $versoes = Get-ChildItem $base -Directory |
            Where-Object { $_.Name -match '^\d+$' } |
            Sort-Object { [int]$_.Name } -Descending
        foreach ($versao in $versoes) {
            $bin = Join-Path $versao.FullName "bin"
            if (Test-Path (Join-Path $bin "pg_restore.exe")) { return $bin }
        }
    }
    return $null
}

function Testar-Conexao($usuario, $porta) {
    # -h 127.0.0.1 explicito: sem isso o libpq tenta "localhost", que pode
    # resolver para ::1 e cair em outra regra do pg_hba.conf.
    # -w impede o prompt interativo: a saida esta redirecionada, e sem isso o
    # script ficaria travado esperando uma senha que o usuario nao ve sendo pedida.
    & psql -w -U $usuario -h 127.0.0.1 -p $porta -d postgres -c "SELECT 1" *> $null
    return ($LASTEXITCODE -eq 0)
}

function Pedir-Senha($usuario) {
    $segura = Read-Host "Senha do usuario '$usuario' do PostgreSQL" -AsSecureString
    return [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($segura))
}

# ---------------------------------------------------------------- requisitos

$python = Achar-Python
if (-not $python) {
    Write-Host "Falta o Python 3.12 ou superior." -ForegroundColor Red
    Write-Host "Instale com:  winget install Python.Python.3.12"
    Write-Host "ou baixe em:  https://www.python.org/downloads/windows/"
    Write-Host "Feche e reabra o terminal depois de instalar."
    exit 1
}
Write-Host "Python encontrado: $python" -ForegroundColor Green

$pastaPg = Achar-Pasta-Postgres
if ($null -eq $pastaPg) {
    Write-Host "Falta o PostgreSQL (versao 17 ou superior)." -ForegroundColor Red
    Write-Host "Instale com:  winget install PostgreSQL.PostgreSQL.17"
    Write-Host "ou baixe em:  https://www.postgresql.org/download/windows/"
    Write-Host ""
    Write-Host "Durante a instalacao, anote a senha do usuario 'postgres'."
    Write-Host "A versao 17 e necessaria para restaurar o BackupNutriJR."
    Write-Host "Feche e reabra o terminal depois de instalar."
    exit 1
}
if ($pastaPg -ne "") {
    $env:Path = "$pastaPg;$env:Path"
    Write-Host "PostgreSQL encontrado em: $pastaPg" -ForegroundColor Green
} else {
    Write-Host "PostgreSQL encontrado no PATH" -ForegroundColor Green
}

$versaoCliente = [int](((& psql --version) -replace '[^\d.]', '') -split '\.')[0]
Write-Host "Cliente psql: versao $versaoCliente | porta escolhida: $Porta" -ForegroundColor Green
if ($versaoCliente -lt 17 -and $Backup) {
    Write-Host ""
    Write-Host "Atencao: o cliente PostgreSQL e a versao $versaoCliente." -ForegroundColor Yellow
    Write-Host "O BackupNutriJR foi gerado com pg_dump 17 e nao e restauravel por versoes"
    Write-Host "anteriores (erro 'unsupported version'). Instale a 17:"
    Write-Host "  winget install PostgreSQL.PostgreSQL.17"
    Write-Host "Ela convivera com a instalacao atual, normalmente na porta 5433:"
    Write-Host "  .\scripts\preparar_local_sem_docker.ps1 backups\BackupNutriJR -Porta 5433"
    Write-Host ""
    $resposta = Read-Host "Tentar mesmo assim? (s/N)"
    if ($resposta -notmatch '^[sS]') { exit 1 }
}

if ($Backup -and -not (Test-Path $Backup)) {
    Write-Host "erro: arquivo '$Backup' nao encontrado." -ForegroundColor Red
    Write-Host "Exemplo:  Copy-Item ..\Nutri_Jr\BackupNutriJR backups\"
    exit 1
}

# ------------------------------------------------------- ambiente virtual

if (-not (Test-Path ".venv")) {
    Write-Host "==> criando o ambiente virtual" -ForegroundColor Cyan
    & $python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "falha ao criar o ambiente virtual" }
}
$py = ".\.venv\Scripts\python.exe"

Write-Host "==> instalando as dependencias" -ForegroundColor Cyan
& $py -m pip install --quiet --upgrade pip
& $py -m pip install --quiet -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { throw "falha ao instalar as dependencias" }

# --------------------------------------------------------------- banco

# A senha e sempre VALIDADA contra o servidor. Uma PGPASSWORD herdada da sessao
# (de outro script ou de uma configuracao antiga) nao e aceita sem teste: era o
# que fazia o script falhar sem nem pedir a senha.
if ($env:PGPASSWORD) {
    Write-Host "==> testando a senha ja presente em PGPASSWORD" -ForegroundColor Cyan
    if (-not (Testar-Conexao $UsuarioDb $Porta)) {
        Write-Host "   a senha em PGPASSWORD nao serve; vou pedir a correta." -ForegroundColor Yellow
        Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    }
}

$tentativas = 0
while (-not $env:PGPASSWORD -or -not (Testar-Conexao $UsuarioDb $Porta)) {
    $tentativas++
    if ($tentativas -gt 3) {
        Write-Host ""
        Write-Host "Nao foi possivel autenticar no PostgreSQL." -ForegroundColor Red
        Write-Host "Verifique o servico (Get-Service *postgres*), a porta (-Porta) e a senha."
        Write-Host "Para redefinir a senha, veja a secao 'Senha do PostgreSQL' no README."
        exit 1
    }
    $env:PGPASSWORD = Pedir-Senha $UsuarioDb
    if (-not $env:PGPASSWORD) {
        Write-Host "   senha vazia." -ForegroundColor Yellow
        continue
    }
    if (Testar-Conexao $UsuarioDb $Porta) { break }
    Write-Host "   senha incorreta." -ForegroundColor Yellow
}
Write-Host "Conexao com o PostgreSQL confirmada." -ForegroundColor Green

# A senha vai codificada na URL: simbolos como @ : / # quebrariam a conexao.
$senhaUrl = [uri]::EscapeDataString($env:PGPASSWORD)
$usuarioUrl = [uri]::EscapeDataString($UsuarioDb)
$env:DATABASE_URL = "postgres://${usuarioUrl}:${senhaUrl}@127.0.0.1:$Porta/$Banco"
$env:DJANGO_SETTINGS_MODULE = "config.settings.dev"

if ($Backup) {
    Write-Host "==> recriando o banco '$Banco'" -ForegroundColor Cyan
    & dropdb -w -U $UsuarioDb -h 127.0.0.1 -p $Porta --if-exists --force $Banco
    & createdb -w -U $UsuarioDb -h 127.0.0.1 -p $Porta $Banco
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "Nao foi possivel criar o banco." -ForegroundColor Red
        Write-Host "Causas comuns: senha incorreta, servico parado ou porta errada."
        Write-Host "  servicos:  Get-Service *postgres*"
        Write-Host "  esqueceu a senha? veja a secao 'Senha do PostgreSQL' no README"
        throw "falha ao criar o banco"
    }

    Write-Host "==> restaurando o backup (o arquivo original nao e alterado)" -ForegroundColor Cyan
    # O -e (--exit-on-error) nao e usado de proposito: o dump traz objetos que nao
    # se aplicam a uma instalacao local (extensao pg_stat_statements, comentario do
    # schema public, propriedades do banco do Heroku). Esses erros sao inofensivos,
    # e as tabelas e os dados sao restaurados normalmente.
    & pg_restore -w --no-owner --no-privileges -U $UsuarioDb -h 127.0.0.1 -p $Porta -d $Banco $Backup
    Write-Host "   (mensagens sobre extensao/comentario/propriedades acima sao esperadas)"

    # Em vez de confiar nos avisos, confere se os dados chegaram de fato.
    Write-Host "==> verificando o conteudo restaurado" -ForegroundColor Cyan
    $fichas = (& psql -w -At -U $UsuarioDb -h 127.0.0.1 -p $Porta -d $Banco `
        -c "SELECT count(*) FROM fichas_ficha").Trim()
    $ingredientes = (& psql -w -At -U $UsuarioDb -h 127.0.0.1 -p $Porta -d $Banco `
        -c "SELECT count(*) FROM fichas_ingrediente").Trim()
    if (-not $fichas -or [int]$fichas -eq 0) {
        Write-Host "A restauracao nao trouxe fichas." -ForegroundColor Red
        Write-Host "Verifique as mensagens do pg_restore acima (o cliente precisa ser 17+)."
        throw "restauracao sem dados"
    }
    Write-Host "   $fichas fichas e $ingredientes ingredientes no banco" -ForegroundColor Green

    Write-Host "==> reconhecendo o schema legado" -ForegroundColor Cyan
    & $py manage.py migrate --fake-initial --noinput

    Write-Host "==> saneamento (relatorio, nada e gravado)" -ForegroundColor Cyan
    & $py manage.py sanear_backup --dry-run
    Write-Host "==> saneamento (aplicando)" -ForegroundColor Cyan
    & $py manage.py sanear_backup

    Write-Host ""
    Write-Host "Acervo restaurado." -ForegroundColor Green
    Write-Host "Os usuarios sao os reais do backup. Para criar um acesso local:"
    Write-Host "  .\.venv\Scripts\python.exe manage.py createsuperuser"
} else {
    & createdb -w -U $UsuarioDb -h 127.0.0.1 -p $Porta $Banco 2>$null
    Write-Host "==> aplicando as migrations" -ForegroundColor Cyan
    & $py manage.py migrate --noinput

    $senhaAdmin = if ($env:INSTANCIA_ADMIN_SENHA) { $env:INSTANCIA_ADMIN_SENHA } else { "admin-local-123456" }
    $env:INSTANCIA_ADMIN_SENHA = $senhaAdmin
    Write-Host "==> configurando a instancia" -ForegroundColor Cyan
    & $py manage.py bootstrap_instancia --nome "Nutri Local" --admin admin --chave CHAVE-LOCAL
    if ($LASTEXITCODE -ne 0) {
        Write-Host "(instancia ja estava configurada - nada a fazer)" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "Instancia nova pronta." -ForegroundColor Green
    Write-Host "  usuario: admin"
    Write-Host "  senha:   $senhaAdmin"
    Write-Host "  chave de cadastro: CHAVE-LOCAL"
}

Write-Host ""
Write-Host "Iniciando o servidor em http://localhost:8000 (Ctrl+C para parar)" -ForegroundColor Green
Write-Host ""
& $py manage.py runserver
