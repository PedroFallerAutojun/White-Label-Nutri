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
    return problemas


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
