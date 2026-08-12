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

# ------------------------------------------------------------------- funcoes

function Executar {
    # Executa um programa externo e devolve o codigo de saida.
    #
    # Necessario porque, com $ErrorActionPreference = "Stop", qualquer texto que um
    # programa escreva em stderr vira erro FATAL no PowerShell, mesmo redirecionado.
    # psql e pg_restore usam stderr para avisos normais, o que derrubava o script
    # mesmo quando tudo estava correto.
    param(
        [Parameter(Mandatory = $true)][string]$Programa,
        [string[]]$Argumentos = @(),
        [switch]$Silencioso
    )

    $anterior = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        if ($Silencioso) {
            & $Programa @Argumentos 2>&1 | Out-Null
        } else {
            & $Programa @Argumentos 2>&1 | ForEach-Object { Write-Host "   $_" }
        }
        return $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $anterior
    }
}

function Capturar {
    # Igual a Executar, mas devolve a saida do programa em vez do codigo.
    param(
        [Parameter(Mandatory = $true)][string]$Programa,
        [string[]]$Argumentos = @()
    )
    $anterior = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $saida = (& $Programa @Argumentos 2>$null)
    } finally {
        $ErrorActionPreference = $anterior
    }
    if ($LASTEXITCODE -ne 0) { return $null }
    return ("$saida").Trim()
}

function Achar-Python {
    foreach ($candidato in @("py", "python", "python3")) {
        if (-not (Get-Command $candidato -ErrorAction SilentlyContinue)) { continue }
        $versao = Capturar -Programa $candidato -Argumentos @(
            "-c", "import sys; print('%d.%d' % sys.version_info[:2])")
        if ($versao -and [version]$versao -ge [version]"3.12") { return $candidato }
    }
    return $null
}

function Achar-Pasta-Postgres {
    # Primeiro no PATH; depois nas pastas padrao de instalacao do Windows.
    if (Get-Command pg_restore -ErrorAction SilentlyContinue) { return "" }
    foreach ($base in @("$env:ProgramFiles\PostgreSQL", "${env:ProgramFiles(x86)}\PostgreSQL")) {
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
    # -w impede o prompt interativo de senha: sem ele o script travaria em
    # silencio, porque a saida esta suprimida.
    $codigo = Executar -Programa "psql" -Silencioso -Argumentos @(
        "-w", "-U", $usuario, "-h", "127.0.0.1", "-p", "$porta", "-d", "postgres",
        "-c", "SELECT 1")
    return ($codigo -eq 0)
}

function Pedir-Senha($usuario) {
    $segura = Read-Host "Senha do usuario '$usuario' do PostgreSQL" -AsSecureString
    return [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($segura))
}

function Consultar($usuario, $porta, $banco, $sql) {
    return Capturar -Programa "psql" -Argumentos @(
        "-w", "-At", "-U", $usuario, "-h", "127.0.0.1", "-p", "$porta", "-d", $banco,
        "-c", $sql)
}

# --------------------------------------------------------------- requisitos

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

$textoVersao = Capturar -Programa "psql" -Argumentos @("--version")
$versaoCliente = [int]((("$textoVersao") -replace '[^\d.]', '') -split '\.')[0]
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
    if ((Read-Host "Tentar mesmo assim? (s/N)") -notmatch '^[sS]') { exit 1 }
}

if ($Backup -and -not (Test-Path $Backup)) {
    Write-Host "erro: arquivo '$Backup' nao encontrado." -ForegroundColor Red
    Write-Host "Exemplo:  Copy-Item ..\Nutri_Jr\BackupNutriJR backups\"
    exit 1
}

# ---------------------------------------------------------- ambiente virtual

if (-not (Test-Path ".venv")) {
    Write-Host "==> criando o ambiente virtual" -ForegroundColor Cyan
    if ((Executar -Programa $python -Argumentos @("-m", "venv", ".venv")) -ne 0) {
        throw "falha ao criar o ambiente virtual"
    }
}
$py = ".\.venv\Scripts\python.exe"

Write-Host "==> instalando as dependencias" -ForegroundColor Cyan
Executar -Programa $py -Silencioso -Argumentos @(
    "-m", "pip", "install", "--quiet", "--upgrade", "pip") | Out-Null
if ((Executar -Programa $py -Silencioso -Argumentos @(
        "-m", "pip", "install", "--quiet", "-r", "requirements-dev.txt")) -ne 0) {
    throw "falha ao instalar as dependencias"
}

# ------------------------------------------------------------------ conexao

# A senha e sempre VALIDADA contra o servidor: uma PGPASSWORD herdada da sessao
# (de outro script ou de configuracao antiga) nao e aceita sem teste.
if ($env:PGPASSWORD) {
    Write-Host "==> testando a senha presente em PGPASSWORD" -ForegroundColor Cyan
    if (Testar-Conexao $UsuarioDb $Porta) {
        Write-Host "   serve" -ForegroundColor Green
    } else {
        Write-Host "   nao serve; vou pedir a senha correta" -ForegroundColor Yellow
        Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    }
}

$tentativas = 0
while (-not ($env:PGPASSWORD -and (Testar-Conexao $UsuarioDb $Porta))) {
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
        Write-Host "   senha vazia" -ForegroundColor Yellow
    } elseif (-not (Testar-Conexao $UsuarioDb $Porta)) {
        Write-Host "   senha incorreta" -ForegroundColor Yellow
    }
}
Write-Host "Conexao com o PostgreSQL confirmada." -ForegroundColor Green

# A senha vai codificada na URL: simbolos como @ : / # quebrariam a conexao.
$senhaUrl = [uri]::EscapeDataString($env:PGPASSWORD)
$usuarioUrl = [uri]::EscapeDataString($UsuarioDb)
$env:DATABASE_URL = "postgres://${usuarioUrl}:${senhaUrl}@127.0.0.1:$Porta/$Banco"
$env:DJANGO_SETTINGS_MODULE = "config.settings.dev"

$comuns = @("-w", "-U", $UsuarioDb, "-h", "127.0.0.1", "-p", "$Porta")

# --------------------------------------------------------------------- banco

if ($Backup) {
    Write-Host "==> recriando o banco '$Banco'" -ForegroundColor Cyan
    Executar -Programa "dropdb" -Silencioso -Argumentos (
        $comuns + @("--if-exists", "--force", $Banco)) | Out-Null
    if ((Executar -Programa "createdb" -Argumentos ($comuns + @($Banco))) -ne 0) {
        Write-Host ""
        Write-Host "Nao foi possivel criar o banco." -ForegroundColor Red
        Write-Host "Causas comuns: servico parado ou porta errada (-Porta)."
        Write-Host "  servicos:  Get-Service *postgres*"
        throw "falha ao criar o banco"
    }

    Write-Host "==> restaurando o backup (o arquivo original nao e alterado)" -ForegroundColor Cyan
    # O dump traz objetos que nao se aplicam a uma instalacao local (extensao
    # pg_stat_statements, comentario do schema public, propriedades do banco do
    # Heroku). Esses erros sao inofensivos: tabelas e dados entram normalmente.
    Executar -Programa "pg_restore" -Argumentos (
        $comuns + @("--no-owner", "--no-privileges", "-d", $Banco, $Backup)) | Out-Null
    Write-Host "   (mensagens sobre extensao/comentario/propriedades acima sao esperadas)"

    Write-Host "==> verificando o conteudo restaurado" -ForegroundColor Cyan
    $fichas = Consultar $UsuarioDb $Porta $Banco "SELECT count(*) FROM fichas_ficha"
    $ingredientes = Consultar $UsuarioDb $Porta $Banco "SELECT count(*) FROM fichas_ingrediente"
    if (-not $fichas -or [int]$fichas -eq 0) {
        Write-Host "A restauracao nao trouxe fichas." -ForegroundColor Red
        Write-Host "Veja as mensagens do pg_restore acima (o cliente precisa ser 17+)."
        throw "restauracao sem dados"
    }
    Write-Host "   $fichas fichas e $ingredientes ingredientes no banco" -ForegroundColor Green

    Write-Host "==> reconhecendo o schema legado" -ForegroundColor Cyan
    if ((Executar -Programa $py -Argumentos @(
            "manage.py", "migrate", "--fake-initial", "--noinput")) -ne 0) {
        throw "falha ao aplicar as migrations"
    }

    Write-Host "==> saneamento (relatorio, nada e gravado)" -ForegroundColor Cyan
    Executar -Programa $py -Argumentos @("manage.py", "sanear_backup", "--dry-run") | Out-Null
    Write-Host "==> saneamento (aplicando)" -ForegroundColor Cyan
    if ((Executar -Programa $py -Argumentos @("manage.py", "sanear_backup")) -ne 0) {
        throw "falha no saneamento"
    }

    Write-Host ""
    Write-Host "Acervo restaurado." -ForegroundColor Green
    Write-Host "Os usuarios sao os reais do backup. Para criar um acesso local, em"
    Write-Host "outro terminal:  .\.venv\Scripts\python.exe manage.py createsuperuser"
} else {
    Executar -Programa "createdb" -Silencioso -Argumentos ($comuns + @($Banco)) | Out-Null

    Write-Host "==> aplicando as migrations" -ForegroundColor Cyan
    if ((Executar -Programa $py -Argumentos @("manage.py", "migrate", "--noinput")) -ne 0) {
        throw "falha ao aplicar as migrations"
    }

    $senhaAdmin = if ($env:INSTANCIA_ADMIN_SENHA) { $env:INSTANCIA_ADMIN_SENHA } else { "admin-local-123456" }
    $env:INSTANCIA_ADMIN_SENHA = $senhaAdmin
    Write-Host "==> configurando a instancia" -ForegroundColor Cyan
    if ((Executar -Programa $py -Argumentos @(
            "manage.py", "bootstrap_instancia", "--nome", "Nutri Local",
            "--admin", "admin", "--chave", "CHAVE-LOCAL")) -ne 0) {
        Write-Host "(instancia ja estava configurada - nada a fazer)" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "Instancia nova pronta." -ForegroundColor Green
    Write-Host "  usuario: admin"
    Write-Host "  senha:   $senhaAdmin"
    Write-Host "  chave de cadastro: CHAVE-LOCAL"
}

Write-Host ""
Write-Host "Servidor em http://localhost:8000 (Ctrl+C para parar)" -ForegroundColor Green
Write-Host ""
Executar -Programa $py -Argumentos @("manage.py", "runserver") | Out-Null
