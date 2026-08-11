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

function Testar-DockerCompose {
    docker compose version *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "'docker compose' nao respondeu. O Docker Desktop esta aberto e rodando?"
    }
}

function Aguardar-Banco {
    Write-Host "==> aguardando o banco" -ForegroundColor Cyan
    foreach ($tentativa in 1..60) {
        docker compose exec -T db pg_isready -U $usuarioDb *> $null
        if ($LASTEXITCODE -eq 0) { return }
        Start-Sleep -Seconds 1
    }
    throw "o banco nao ficou disponivel."
}

function Invocar($descricao, [scriptblock]$comando) {
    Write-Host "==> $descricao" -ForegroundColor Cyan
    & $comando
    if ($LASTEXITCODE -ne 0) { throw "falhou: $descricao" }
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
    Invocar "subindo apenas o banco (a aplicacao sobe depois)" { docker compose up -d --build db }
    Aguardar-Banco

    $arquivo = "/backups/" + (Split-Path $Backup -Leaf)
    Invocar "removendo o banco anterior" {
        docker compose exec -T db dropdb -U $usuarioDb --if-exists --force $banco
    }
    Invocar "criando o banco" { docker compose exec -T db createdb -U $usuarioDb $banco }
    Invocar "restaurando $arquivo (o arquivo original nao e alterado)" {
        docker compose exec -T db pg_restore --no-owner --no-privileges -U $usuarioDb -d $banco $arquivo
    }

    # Confere se os dados chegaram, em vez de confiar nos avisos do pg_restore.
    Write-Host "==> verificando o conteudo restaurado" -ForegroundColor Cyan
    $fichas = (docker compose exec -T db psql -w -At -U $usuarioDb -d $banco -c "SELECT count(*) FROM fichas_ficha").Trim()
    if (-not $fichas -or [int]$fichas -eq 0) {
        throw "a restauracao nao trouxe fichas; veja as mensagens do pg_restore acima"
    }
    Write-Host "   $fichas fichas no banco" -ForegroundColor Green

    # O entrypoint do web aplica migrate --fake-initial, reconhecendo o schema legado.
    Invocar "subindo a aplicacao" { docker compose up -d --build web }

    Invocar "saneamento (relatorio, nada e gravado)" {
        docker compose exec -T web python manage.py sanear_backup --dry-run
    }
    Invocar "saneamento (aplicando)" {
        docker compose exec -T web python manage.py sanear_backup
    }

    Write-Host ""
    Write-Host "Acervo restaurado. Entre com um usuario existente da instancia." -ForegroundColor Green
    Write-Host "Para criar um acesso local, rode:"
    Write-Host "  docker compose exec web python manage.py createsuperuser"
}
else {
    Invocar "subindo os servicos" { docker compose up -d --build }
    Aguardar-Banco

    $senha  = if ($env:INSTANCIA_ADMIN_SENHA) { $env:INSTANCIA_ADMIN_SENHA } else { "admin-local-123456" }
    $nome   = if ($env:NOME_INSTANCIA)        { $env:NOME_INSTANCIA }        else { "Nutri Local" }
    $admin  = if ($env:ADMIN_INSTANCIA)       { $env:ADMIN_INSTANCIA }       else { "admin" }
    $chave  = if ($env:CHAVE_CADASTRO)        { $env:CHAVE_CADASTRO }        else { "CHAVE-LOCAL" }

    Write-Host "==> configurando a instancia" -ForegroundColor Cyan
    docker compose exec -T -e "INSTANCIA_ADMIN_SENHA=$senha" web python manage.py bootstrap_instancia --nome $nome --admin $admin --chave $chave
    if ($LASTEXITCODE -ne 0) {
        Write-Host "(instancia ja estava configurada - nada a fazer)" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "Instancia nova pronta." -ForegroundColor Green
    Write-Host "  usuario: $admin"
    Write-Host "  senha:   $senha"
    Write-Host "  chave de cadastro: $chave"
}

Write-Host "Aplicacao: http://localhost:$portaWeb" -ForegroundColor Green
