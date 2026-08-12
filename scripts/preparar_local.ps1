# Prepara o ambiente local com Docker no Windows (PowerShell).
#
#   .\scripts\preparar_local.ps1                          # instancia nova (vazia)
#   .\scripts\preparar_local.ps1 backups\BackupNutriJR     # restaura o acervo legado
#
# Equivalente ao scripts/preparar_local.sh (Linux/macOS).

param(
    [string]$Backup = ""
)

$ErrorActionPreference = "Stop"

# Roda a partir da raiz do projeto, independente de onde foi chamado.
Set-Location (Join-Path $PSScriptRoot "..")

$usuarioDb = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "postgres" }
$banco     = if ($env:POSTGRES_DB)   { $env:POSTGRES_DB }   else { "nutri" }
$portaWeb  = if ($env:PORTA_WEB)     { $env:PORTA_WEB }     else { "8000" }

function Executar {
    # Executa um programa externo e devolve o codigo de saida.
    #
    # Necessario porque, com $ErrorActionPreference = "Stop", qualquer texto que um
    # programa escreva em stderr vira erro FATAL no PowerShell, mesmo redirecionado.
    # docker, psql e pg_restore usam stderr para mensagens normais.
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
    # Igual a Executar, mas devolve a saida em vez do codigo.
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

function Testar-DockerCompose {
    if ((Executar -Programa "docker" -Silencioso -Argumentos @("compose", "version")) -ne 0) {
        throw "'docker compose' nao respondeu. O Docker Desktop esta aberto e rodando?"
    }
}

function Aguardar-Banco {
    Write-Host "==> aguardando o banco" -ForegroundColor Cyan
    foreach ($tentativa in 1..60) {
        $codigo = Executar -Programa "docker" -Silencioso -Argumentos @(
            "compose", "exec", "-T", "db", "pg_isready", "-U", $usuarioDb)
        if ($codigo -eq 0) { return }
        Start-Sleep -Seconds 1
    }
    throw "o banco nao ficou disponivel."
}

function Compor($descricao, [string[]]$argumentos) {
    Write-Host "==> $descricao" -ForegroundColor Cyan
    if ((Executar -Programa "docker" -Argumentos (@("compose") + $argumentos)) -ne 0) {
        throw "falhou: $descricao"
    }
}

Testar-DockerCompose

if ($Backup) {
    if (-not (Test-Path $Backup)) {
        Write-Host "erro: arquivo '$Backup' nao encontrado." -ForegroundColor Red
        Write-Host "Copie o backup para a pasta backups\ e informe o caminho, por exemplo:"
        Write-Host "  Copy-Item ..\Nutri_Jr\BackupNutriJR backups\"
        Write-Host "  .\scripts\preparar_local.ps1 backups\BackupNutriJR"
        exit 1
    }

    # A restauracao recria o banco: com a aplicacao conectada, o dropdb falharia.
    Compor "subindo apenas o banco (a aplicacao sobe depois)" @("up", "-d", "--build", "db")
    Aguardar-Banco

    $arquivo = "/backups/" + (Split-Path $Backup -Leaf)
    Compor "removendo o banco anterior" @(
        "exec", "-T", "db", "dropdb", "-w", "-U", $usuarioDb, "--if-exists", "--force", $banco)
    Compor "criando o banco" @("exec", "-T", "db", "createdb", "-w", "-U", $usuarioDb, $banco)
    Compor "restaurando $arquivo (o arquivo original nao e alterado)" @(
        "exec", "-T", "db", "pg_restore", "-w", "--no-owner", "--no-privileges",
        "-U", $usuarioDb, "-d", $banco, $arquivo)

    # Confere se os dados chegaram, em vez de confiar nos avisos do pg_restore.
    Write-Host "==> verificando o conteudo restaurado" -ForegroundColor Cyan
    $fichas = Capturar -Programa "docker" -Argumentos @(
        "compose", "exec", "-T", "db", "psql", "-w", "-At", "-U", $usuarioDb,
        "-d", $banco, "-c", "SELECT count(*) FROM fichas_ficha")
    if (-not $fichas -or [int]$fichas -eq 0) {
        throw "a restauracao nao trouxe fichas; veja as mensagens do pg_restore acima"
    }
    Write-Host "   $fichas fichas no banco" -ForegroundColor Green

    # O entrypoint do web aplica migrate --fake-initial, reconhecendo o schema legado.
    Compor "subindo a aplicacao" @("up", "-d", "--build", "web")

    Compor "saneamento (relatorio, nada e gravado)" @(
        "exec", "-T", "web", "python", "manage.py", "sanear_backup", "--dry-run")
    Compor "saneamento (aplicando)" @(
        "exec", "-T", "web", "python", "manage.py", "sanear_backup")

    Write-Host ""
    Write-Host "Acervo restaurado. Entre com um usuario existente da instancia." -ForegroundColor Green
    Write-Host "Para criar um acesso local, rode:"
    Write-Host "  docker compose exec web python manage.py createsuperuser"
}
else {
    Compor "subindo os servicos" @("up", "-d", "--build")
    Aguardar-Banco

    $senha  = if ($env:INSTANCIA_ADMIN_SENHA) { $env:INSTANCIA_ADMIN_SENHA } else { "admin-local-123456" }
    $nome   = if ($env:NOME_INSTANCIA)        { $env:NOME_INSTANCIA }        else { "Nutri Local" }
    $admin  = if ($env:ADMIN_INSTANCIA)       { $env:ADMIN_INSTANCIA }       else { "admin" }
    $chave  = if ($env:CHAVE_CADASTRO)        { $env:CHAVE_CADASTRO }        else { "CHAVE-LOCAL" }

    Write-Host "==> configurando a instancia" -ForegroundColor Cyan
    $codigo = Executar -Programa "docker" -Argumentos @(
        "compose", "exec", "-T", "-e", "INSTANCIA_ADMIN_SENHA=$senha", "web",
        "python", "manage.py", "bootstrap_instancia", "--nome", $nome,
        "--admin", $admin, "--chave", $chave)
    if ($codigo -ne 0) {
        Write-Host "(instancia ja estava configurada - nada a fazer)" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "Instancia nova pronta." -ForegroundColor Green
    Write-Host "  usuario: $admin"
    Write-Host "  senha:   $senha"
    Write-Host "  chave de cadastro: $chave"
}

Write-Host "Aplicacao: http://localhost:$portaWeb" -ForegroundColor Green
