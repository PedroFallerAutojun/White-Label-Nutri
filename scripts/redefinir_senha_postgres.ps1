# Redefine a senha do usuario 'postgres' numa instalacao local do PostgreSQL.
#
#   Abra o PowerShell COMO ADMINISTRADOR e rode:
#     .\scripts\redefinir_senha_postgres.ps1 -NovaSenha "minhaSenha123"
#
# Como funciona: o PostgreSQL nao permite recuperar a senha, apenas trocar. Para
# isso, a autenticacao local e liberada temporariamente (metodo "trust"), a senha
# e alterada e a configuracao ORIGINAL e restaurada em seguida.
#
# A restauracao acontece mesmo se algo falhar no meio (bloco finally): deixar o
# banco em "trust" permitiria acesso local sem senha.

param(
    [Parameter(Mandatory = $true)][string]$NovaSenha,
    [string]$Versao = "",
    [string]$Usuario = "postgres"
)

$ErrorActionPreference = "Stop"

# ------------------------------------------------------------------ funcoes

function Reiniciar-Postgres($nomeServico, $pastaDados) {
    # Para, espera de fato parar e inicia. Se nao subir, mostra o log do
    # PostgreSQL, que diz o motivo exato.
    Stop-Service $nomeServico -Force -ErrorAction SilentlyContinue
    for ($i = 0; $i -lt 30; $i++) {
        if ((Get-Service $nomeServico).Status -eq "Stopped") { break }
        Start-Sleep -Seconds 1
    }
    try {
        Start-Service $nomeServico -ErrorAction Stop
    } catch {
        Write-Host ""
        Write-Host "O servico do PostgreSQL nao iniciou." -ForegroundColor Red
        $log = Get-ChildItem (Join-Path $pastaDados "log") -Filter *.log -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($log) {
            Write-Host "Ultimas linhas de $($log.FullName):" -ForegroundColor Yellow
            Get-Content $log.FullName -Tail 15 | ForEach-Object { Write-Host "  $_" }
        }
        return $false
    }
    return $true
}

function Achar-Psql($pastaDados) {
    # 1) no PATH
    $noPath = Get-Command psql -ErrorAction SilentlyContinue
    if ($noPath) { return $noPath.Source }

    # 2) irmao da pasta de dados: ...\PostgreSQL\17\data -> ...\PostgreSQL\17\bin
    $raizInstalacao = Split-Path $pastaDados -Parent
    $candidato = Join-Path $raizInstalacao "bin\psql.exe"
    if (Test-Path $candidato) { return $candidato }

    # 3) varredura nas pastas padrao
    foreach ($base in @("$env:ProgramFiles\PostgreSQL", "${env:ProgramFiles(x86)}\PostgreSQL")) {
        if (-not (Test-Path $base)) { continue }
        $achado = Get-ChildItem $base -Directory -ErrorAction SilentlyContinue |
            ForEach-Object { Join-Path $_.FullName "bin\psql.exe" } |
            Where-Object { Test-Path $_ } |
            Select-Object -First 1
        if ($achado) { return $achado }
    }
    return $null
}

# ------------------------------------------------------------- verificacoes


$souAdmin = ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()
).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $souAdmin) {
    Write-Host "Este script precisa de PowerShell como Administrador." -ForegroundColor Red
    Write-Host "Feche este terminal, clique com o botao direito no PowerShell e"
    Write-Host "escolha 'Executar como administrador'."
    exit 1
}

$servicos = Get-CimInstance Win32_Service -Filter "Name like 'postgresql%'"
if (-not $servicos) {
    Write-Host "Nenhum servico do PostgreSQL encontrado nesta maquina." -ForegroundColor Red
    exit 1
}
if ($Versao) {
    $servicos = $servicos | Where-Object { $_.Name -match $Versao }
    if (-not $servicos) {
        Write-Host "Nenhum servico do PostgreSQL para a versao '$Versao'." -ForegroundColor Red
        exit 1
    }
}
$servico = @($servicos)[0]
if (@($servicos).Count -gt 1) {
    Write-Host "Varios servicos encontrados:" -ForegroundColor Yellow
    $servicos | ForEach-Object { Write-Host "  - $($_.Name)" }
    Write-Host "Usando '$($servico.Name)'. Para escolher outro, informe -Versao."
}

# O caminho dos dados vem do proprio servico (-D "..."), o que funciona mesmo
# quando a instalacao nao esta na pasta padrao.
if ($servico.PathName -match '-D\s+"([^"]+)"') {
    $pastaDados = $Matches[1]
} elseif ($servico.PathName -match '-D\s+(\S+)') {
    $pastaDados = $Matches[1]
} else {
    Write-Host "Nao foi possivel descobrir a pasta de dados do servico." -ForegroundColor Red
    exit 1
}

$hba = Join-Path $pastaDados "pg_hba.conf"
if (-not (Test-Path $hba)) {
    Write-Host "Arquivo de configuracao nao encontrado: $hba" -ForegroundColor Red
    exit 1
}

$psql = Achar-Psql $pastaDados
if (-not $psql) {
    Write-Host "Nao foi possivel localizar o psql.exe." -ForegroundColor Red
    Write-Host "Ele costuma ficar em: $env:ProgramFiles\PostgreSQL\17\bin\psql.exe"
    exit 1
}

Write-Host "Servico:        $($servico.Name)"
Write-Host "psql:           $psql"
Write-Host "Configuracao:   $hba"
Write-Host "Usuario alvo:   $Usuario"
Write-Host ""
Write-Host "A autenticacao local sera liberada por alguns segundos e a"
Write-Host "configuracao original sera restaurada ao final."
$resposta = Read-Host "Continuar? (s/N)"
if ($resposta -notmatch '^[sS]') { exit 1 }

# --------------------------------------------------------------- execucao

$backupHba = "$hba.antes-da-troca"
Copy-Item $hba $backupHba -Force
Write-Host "==> copia de seguranca em $backupHba" -ForegroundColor Cyan

try {
    $linhas = Get-Content $hba
    $novas = foreach ($linha in $linhas) {
        if ($linha -match '^\s*#' -or $linha -match '^\s*$') {
            $linha
        } elseif ($linha -match '^\s*(local|host|hostssl|hostnossl)\s') {
            # Troca apenas o metodo de autenticacao (ultima coluna).
            $linha -replace '(scram-sha-256|md5|password|peer|ident|sspi|gss)\s*$', 'trust'
        } else {
            $linha
        }
    }
    # ATENCAO: nao usar Set-Content -Encoding UTF8 aqui. No Windows PowerShell 5.1
    # isso grava um BOM, e o PostgreSQL se recusa a iniciar com BOM no pg_hba.conf
    # ("FATAL: could not load pg_hba.conf"). Gravamos UTF-8 sem BOM.
    $semBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllLines($hba, $novas, $semBom)

    $primeirosBytes = [System.IO.File]::ReadAllBytes($hba)[0..2]
    if ($primeirosBytes[0] -eq 0xEF -and $primeirosBytes[1] -eq 0xBB -and $primeirosBytes[2] -eq 0xBF) {
        throw "o arquivo foi gravado com BOM; abortando antes de reiniciar o servico"
    }

    Write-Host "==> reiniciando o servico" -ForegroundColor Cyan
    if (-not (Reiniciar-Postgres $servico.Name $pastaDados)) {
        throw "o servico nao subiu com a configuracao temporaria"
    }
    Start-Sleep -Seconds 2

    Write-Host "==> alterando a senha" -ForegroundColor Cyan
    $senhaEscapada = $NovaSenha -replace "'", "''"
    & $psql -U $Usuario -d postgres -c "ALTER USER $Usuario PASSWORD '$senhaEscapada'"
    if ($LASTEXITCODE -ne 0) { throw "o comando ALTER USER falhou" }
}
finally {
    # Sempre restaura a configuracao original, mesmo em caso de erro. A copia de
    # seguranca NAO e apagada: se algo der errado, ela e a rede de protecao.
    Write-Host "==> restaurando a configuracao original" -ForegroundColor Cyan
    Copy-Item $backupHba $hba -Force

    if (Reiniciar-Postgres $servico.Name $pastaDados) {
        Write-Host "   servico no ar com a configuracao original" -ForegroundColor Green
        Write-Host "   copia de seguranca mantida em: $backupHba"
    } else {
        Write-Host ""
        Write-Host "IMPORTANTE: a configuracao original foi restaurada em:" -ForegroundColor Yellow
        Write-Host "  $hba"
        Write-Host "A copia de seguranca esta em:"
        Write-Host "  $backupHba"
        Write-Host "Tente iniciar manualmente:"
        Write-Host "  Start-Service $($servico.Name)"
    }
}

# ------------------------------------------------------------- verificacao

Write-Host "==> testando a nova senha" -ForegroundColor Cyan
$env:PGPASSWORD = $NovaSenha
& $psql -U $Usuario -d postgres -c "SELECT version();" *> $null
$ok = ($LASTEXITCODE -eq 0)
$env:PGPASSWORD = $null

Write-Host ""
if ($ok) {
    Write-Host "Senha redefinida com sucesso." -ForegroundColor Green
    Write-Host "A autenticacao por senha voltou a valer (configuracao original restaurada)."
    Write-Host ""
    Write-Host "Agora rode:"
    Write-Host "  .\scripts\preparar_local_sem_docker.ps1 backups\BackupNutriJR"
} else {
    Write-Host "A troca foi executada, mas o teste de conexao falhou." -ForegroundColor Yellow
    Write-Host "Verifique se o servico esta ativo:  Get-Service $($servico.Name)"
}
