#!/usr/bin/env python3
"""Validação estática dos scripts PowerShell do projeto.

Verifica os erros que já nos custaram tempo:
  1. funcao chamada sem estar definida no arquivo;
  2. arquivo sem BOM (o Windows PowerShell 5.1 exige BOM para ler acentos);
  3. caracteres nao-ASCII (evitam qualquer surpresa de codificacao);
  4. chaves e parenteses desbalanceados;
  5. Set-Content -Encoding UTF8 gravando pg_hba.conf (grava BOM e o PostgreSQL
     se recusa a iniciar).

Uso:  python scripts/validar_scripts.py
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Cmdlets e comandos externos usados pelos scripts (nao sao funcoes locais).
CONHECIDOS = {
    "Write-Host", "Read-Host", "Get-Content", "Set-Content", "Copy-Item", "Move-Item",
    "Remove-Item", "Test-Path", "Join-Path", "Split-Path", "Get-Service", "Set-Location",
    "Start-Service", "Stop-Service", "Restart-Service", "Start-Sleep", "Get-Command",
    "Get-ChildItem", "Sort-Object", "Select-Object", "Where-Object", "ForEach-Object",
    "Get-CimInstance", "New-Object", "Out-Null", "Out-String", "Set-ExecutionPolicy",
}


def sem_comentarios_nem_strings(linha: str) -> str:
    """Remove strings e o comentario final, para que parenteses citados em texto
    nao contem como codigo."""
    saida = []
    aspas = None
    for pos, ch in enumerate(linha):
        if aspas:
            if ch == aspas:
                aspas = None
            continue
        if ch in "\"'":
            aspas = ch
            continue
        if ch == "#":
            break
        saida.append(ch)
    return "".join(saida)


def validar(caminho: Path) -> list[str]:
    problemas = []
    bruto = caminho.read_bytes()
    if bruto[:3] != b"\xef\xbb\xbf":
        problemas.append("sem BOM UTF-8 (PowerShell 5.1 lera os acentos errado)")
    texto = bruto.decode("utf-8-sig")

    nao_ascii = sorted({c for c in texto if ord(c) > 127})
    if nao_ascii:
        problemas.append(f"caracteres nao-ASCII: {nao_ascii}")

    codigo = "\n".join(sem_comentarios_nem_strings(l) for l in texto.splitlines())
    for abre, fecha in (("{", "}"), ("(", ")")):
        if codigo.count(abre) != codigo.count(fecha):
            problemas.append(
                f"{abre}{fecha} desbalanceados no codigo: "
                f"{codigo.count(abre)} x {codigo.count(fecha)}"
            )

    definidas = set(re.findall(r"^\s*function\s+([\w-]+)", texto, re.M))
    # Chamadas no estilo Verbo-Substantivo que nao sao cmdlets conhecidos.
    candidatas = set(re.findall(r"(?<![\w.\-])([A-Z][a-z]+-[A-Z][\w-]*)", texto))
    for nome in sorted(candidatas - CONHECIDOS - definidas):
        problemas.append(f"'{nome}' e chamado mas nao esta definido neste arquivo")

    for numero, linha in enumerate(texto.splitlines(), 1):
        if linha.lstrip().startswith("#"):
            continue  # comentarios podem citar o padrao proibido
        if "Set-Content" in linha and "-Encoding UTF8" in linha:
            problemas.append(
                f"linha {numero}: Set-Content -Encoding UTF8 grava BOM no PowerShell 5.1; "
                "use [System.IO.File]::WriteAllLines com UTF8Encoding($false)"
            )

    # Ferramentas do PostgreSQL nao estao no PATH em instalacoes padrao do Windows:
    # ou o script acrescenta o bin ao PATH, ou invoca pelo caminho absoluto (& $psql).
    ajusta_path = "$env:Path =" in texto
    if not ajusta_path:
        ferramentas = r"(psql|pg_restore|pg_dump|createdb|dropdb)"
        for numero, linha in enumerate(texto.splitlines(), 1):
            codigo_linha = sem_comentarios_nem_strings(linha)
            if "docker" in codigo_linha:
                continue  # roda dentro do container, onde as ferramentas existem
            # chamada "pelada": nome sem $ antes e sem .exe, seguido de argumento
            if re.search(rf"(^|[|;&]\s*){ferramentas}\s+-", codigo_linha):
                problemas.append(
                    f"linha {numero}: ferramenta do PostgreSQL chamada sem resolver o "
                    "caminho; no Windows o bin nao esta no PATH por padrao "
                    "(use & $psql ou ajuste $env:Path)"
                )

    # Clientes do PostgreSQL sem -w abrem prompt interativo de senha. Em script
    # com saida redirecionada isso vira travamento silencioso.
    conectam = r"(psql|pg_restore|pg_dump|createdb|dropdb)"
    for numero, linha in enumerate(texto.splitlines(), 1):
        codigo_linha = sem_comentarios_nem_strings(linha)
        if "docker" in codigo_linha or "--version" in codigo_linha:
            continue
        if not re.search(rf"[&$]\s*\$?\w*\b{conectam}\b", codigo_linha):
            continue
        if not re.search(r"\s-U\b|\s-d\b|\s-c\b", codigo_linha):
            continue  # nao esta conectando
        if not re.search(r"\s-w\b", codigo_linha):
            problemas.append(
                f"linha {numero}: cliente do PostgreSQL sem -w; sem essa flag ele "
                "abre prompt de senha e o script trava em silencio"
            )

    # Com $ErrorActionPreference = "Stop", texto em stderr de um programa externo
    # vira erro FATAL no PowerShell (mesmo redirecionado). Chamadas externas devem
    # passar por um ajudante que baixe a preferencia para "Continue".
    if re.search(r'\$ErrorActionPreference\s*=\s*"Stop"', texto):
        seguras = faixas_de_funcoes_seguras(texto)
        externos = r"(psql|pg_restore|pg_dump|createdb|dropdb|docker|pip|py|python)"
        for numero, linha in enumerate(texto.splitlines(), 1):
            codigo_linha = sem_comentarios_nem_strings(linha)
            if not re.search(rf"&\s+\$?\w*{externos}\b|^\s*{externos}\s+\w", codigo_linha):
                continue
            if any(inicio <= numero <= fim for inicio, fim in seguras):
                continue  # dentro do ajudante, que ja ajusta a preferencia
            problemas.append(
                f"linha {numero}: programa externo chamado diretamente com "
                'ErrorActionPreference="Stop"; texto em stderr derruba o script '
                "(use o ajudante Executar/Capturar)"
            )
    return problemas


def faixas_de_funcoes_seguras(texto: str) -> list[tuple[int, int]]:
    """Linhas das funcoes que baixam ErrorActionPreference para "Continue"."""
    linhas = texto.splitlines()
    faixas = []
    for indice, linha in enumerate(linhas):
        if not re.match(r"^\s*function\s+[\w-]+", linha):
            continue
        profundidade = 0
        iniciou = False
        for fim in range(indice, len(linhas)):
            codigo = sem_comentarios_nem_strings(linhas[fim])
            profundidade += codigo.count("{") - codigo.count("}")
            if codigo.count("{"):
                iniciou = True
            if iniciou and profundidade <= 0:
                corpo = "\n".join(linhas[indice:fim + 1])
                if re.search(r'\$ErrorActionPreference\s*=\s*"Continue"', corpo):
                    faixas.append((indice + 1, fim + 1))
                break
    return faixas


def main() -> int:
    scripts = sorted((RAIZ / "scripts").glob("*.ps1"))
    if not scripts:
        print("nenhum script .ps1 encontrado")
        return 1

    total = 0
    for script in scripts:
        problemas = validar(script)
        total += len(problemas)
        if problemas:
            print(f"[FALHA] {script.relative_to(RAIZ)}")
            for problema in problemas:
                print(f"    - {problema}")
        else:
            print(f"[  ok  ] {script.relative_to(RAIZ)}")

    print()
    print("nenhum problema encontrado." if total == 0 else f"{total} problema(s) encontrado(s).")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
