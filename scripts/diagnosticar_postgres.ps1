# Diagnostico da conexao com o PostgreSQL local (Windows).
#
#   .\scripts\diagnosticar_postgres.ps1
#   .\scripts\diagnosticar_postgres.ps1 -Senha 'minhaSenha123'
#
# Reune num so lugar tudo que costuma causar "autenticacao falhou":
# servicos, portas, versao, regras do pg_hba.conf e um teste real de conexao.
# Nao altera nada.

param(
    [string]$Senha = "",
    [string]$Usuario = "postgres",
    [int]$Porta = 5432
)

$ErrorActionPreference = "Stop"

function Executar {
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

Write-Host "=== 1. Servicos do PostgreSQL ===" -ForegroundColor Cyan
$servicos = Get-CimInstance Win32_Service -Filter "Name like 'postgresql%'"
if (-not $servicos) {
    Write-Host "Nenhum servico encontrado." -ForegroundColor Red
    exit 1
}
foreach ($s in $servicos) {
    $cor = if ($s.State -eq "Running") { "Green" } else { "Red" }
    Write-Host "   $($s.Name)  estado: $($s.State)" -ForegroundColor $cor
    if ($s.PathName -match '-D\s+"([^"]+)"') { Write-Host "      dados: $($Matches[1])" }
}
if (@($servicos).Count -gt 1) {
    Write-Host "   ATENCAO: mais de uma instancia. A senha pode ter sido trocada em outra." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== 2. Quem esta escutando na porta $Porta ===" -ForegroundColor Cyan
$conexoes = Get-NetTCPConnection -LocalPort $Porta -State Listen -ErrorAction SilentlyContinue
if (-not $conexoes) {
    Write-Host "   Ninguem escutando na porta $Porta." -ForegroundColor Red
    Write-Host "   Portas dos servicos: veja postgresql.conf na pasta de dados."
} else {
    foreach ($c in $conexoes | Select-Object -Unique OwningProcess) {
        $proc = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
        Write-Host "   PID $($c.OwningProcess): $($proc.Path)"
    }
}

Write-Host ""
Write-Host "=== 3. Cliente psql ===" -ForegroundColor Cyan
$psql = $null
$noPath = Get-Command psql -ErrorAction SilentlyContinue
if ($noPath) {
    $psql = $noPath.Source
} else {
    foreach ($base in @("$env:ProgramFiles\PostgreSQL", "${env:ProgramFiles(x86)}\PostgreSQL")) {
        if (-not (Test-Path $base)) { continue }
        $achado = Get-ChildItem $base -Directory -ErrorAction SilentlyContinue |
            ForEach-Object { Join-Path $_.FullName "bin\psql.exe" } |
            Where-Object { Test-Path $_ } | Select-Object -First 1
        if ($achado) { $psql = $achado; break }
    }
}
if (-not $psql) {
    Write-Host "   psql.exe nao encontrado." -ForegroundColor Red
    exit 1
}
Write-Host "   $psql"
Write-Host "   $(Capturar -Programa $psql -Argumentos @('--version'))"

Write-Host ""
Write-Host "=== 4. Regras de autenticacao (pg_hba.conf) ===" -ForegroundColor Cyan
foreach ($s in $servicos) {
    if ($s.PathName -notmatch '-D\s+"([^"]+)"') { continue }
    $hba = Join-Path $Matches[1] "pg_hba.conf"
    if (-not (Test-Path $hba)) { continue }
    Write-Host "   $hba"
    Get-Content $hba |
        Where-Object { $_ -match '^\s*(local|host|hostssl|hostnossl)\s' } |
        ForEach-Object { Write-Host "      $_" }
}

Write-Host ""
Write-Host "=== 5. Variavel PGPASSWORD nesta sessao ===" -ForegroundColor Cyan
if ($env:PGPASSWORD) {
    Write-Host "   definida, com $($env:PGPASSWORD.Length) caracteres" -ForegroundColor Yellow
    Write-Host "   (se nao for a senha atual, ela atrapalha: Remove-Item Env:PGPASSWORD)"
} else {
    Write-Host "   nao definida"
}

Write-Host ""
Write-Host "=== 6. Teste de conexao ===" -ForegroundColor Cyan
if (-not $Senha) {
    $segura = Read-Host "Senha do usuario '$Usuario' (Enter para usar a PGPASSWORD atual)" -AsSecureString
    $digitada = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($segura))
    if ($digitada) { $Senha = $digitada }
}
if ($Senha) {
    Write-Host "   testando senha com $($Senha.Length) caracteres"
    $env:PGPASSWORD = $Senha
}

$codigo = Executar -Programa $psql -Argumentos @(
    "-w", "-U", $Usuario, "-h", "127.0.0.1", "-p", "$Porta", "-d", "postgres",
    "-c", "SELECT current_user, version()")

Write-Host ""
if ($codigo -eq 0) {
    Write-Host "CONEXAO OK. A senha funciona." -ForegroundColor Green
    Write-Host "Agora rode:"
    Write-Host "  .\scripts\preparar_local_sem_docker.ps1 backups\BackupNutriJR"
} else {
    Write-Host "CONEXAO FALHOU." -ForegroundColor Red
    Write-Host ""
    Write-Host "Coisas a verificar, na ordem:"
    Write-Host " 1. Se voce definiu a senha com aspas DUPLAS e ela contem '\$', o PowerShell"
    Write-Host "    trocou a variavel por vazio: \"senha\$123\" virou 'senha'. Use aspas SIMPLES."
    Write-Host " 2. Se ha mais de um servico na secao 1, a senha pode ter sido trocada em outro."
    Write-Host " 3. Se as regras da secao 4 nao tiverem uma linha para 127.0.0.1, a conexao"
    Write-Host "    local por TCP nao e permitida."
    Write-Host " 4. Para redefinir a senha (PowerShell como Administrador):"
    Write-Host "      .\scripts\redefinir_senha_postgres.ps1 -NovaSenha 'senhaSimples123'"
}
