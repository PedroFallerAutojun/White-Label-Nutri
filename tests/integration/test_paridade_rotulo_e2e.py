"""Paridade ponta a ponta do rótulo renderizado (D-008).

Renderiza a view do rótulo da nova aplicação e compara o conteúdo da tabela
vertical com o que o sistema ORIGINAL produzia, ficha por ficha.

Requer um banco restaurado do backup legado — pula automaticamente quando o
banco de teste não tem o acervo (ex.: CI sem o dump). Para rodar com os dados
reais: DATABASE_URL apontando para a cópia restaurada e
`pytest --reuse-db -k paridade_rotulo_e2e`.
"""
import gzip
import json
import re
from pathlib import Path

import pytest
from django.contrib.auth.models import User

from apps.fichas.models import Ficha

GOLDEN = Path(__file__).resolve().parent.parent / "golden" / "golden_fichax.json.gz"

TABELA_VERTICAL = re.compile(r'<table class="rotulo-vertical">(.*?)</table>', re.S)
LINHA = re.compile(r"<tr>(.*?)</tr>", re.S)
CELULA = re.compile(r"<td[^>]*>(.*?)</td>", re.S)


def _limpa(html):
    return " ".join(re.sub(r"<[^>]+>", "", html).split()).replace("ㅤ", "").strip()


def _linhas_renderizadas(corpo):
    bloco = TABELA_VERTICAL.search(corpo)
    if not bloco:
        return None
    linhas = []
    for linha in LINHA.findall(bloco.group(1)):
        celulas = [_limpa(c) for c in CELULA.findall(linha)]
        if len(celulas) != 4 or celulas[1] == "100g" or celulas[0].startswith("*Percentual"):
            continue
        linhas.append(celulas)
    return linhas


def _linhas_esperadas(ficha_golden):
    linhas = []
    for linha in ficha_golden["linhas"]:
        if len(linha) > 3:
            rotulo = f"{linha[0]} ({linha[3]})"
            por_100g = "" if linha[4] is None else str(linha[4])
        else:
            rotulo, por_100g = linha[0], ""
        porcao = "" if linha[1] is None else str(linha[1])
        vd = "" if linha[2] in (None, "") else str(linha[2])
        linhas.append([rotulo, por_100g, porcao, vd])
    return linhas


@pytest.fixture(scope="module")
def golden():
    with gzip.open(GOLDEN, "rt", encoding="utf-8") as f:
        return json.load(f)["fichas"]


@pytest.mark.django_db
def test_rotulo_renderizado_bate_com_original(client, golden):
    if Ficha.objects.count() < 100:
        pytest.skip("banco sem o acervo legado restaurado")

    user = User.objects.filter(username="admin").first() or User.objects.first()
    client.force_login(user)

    divergencias = []
    verificadas = 0
    for pk_str, esperado in golden.items():
        pk = int(pk_str)
        if not Ficha.objects.filter(pk=pk).exists():
            continue
        resp = client.get(f"/fichaX/{pk}")
        if resp.status_code != 200:
            divergencias.append((pk, "http", resp.status_code))
            continue
        corpo = resp.content.decode()
        minhas = _linhas_renderizadas(corpo)
        delas = _linhas_esperadas(esperado)
        if len(minhas or []) != len(delas):
            divergencias.append((pk, "num_linhas", len(minhas or []), len(delas)))
            continue
        for minha, dela in zip(minhas, delas):
            # B3 corrigido: o golden traz o valor bugado do Manganês por 100 g
            if minha != dela and not minha[0].startswith("Manganês"):
                divergencias.append((pk, "linha", minha, dela))
        if esperado["numPorcoesExibicao"] not in corpo:
            divergencias.append((pk, "numPorcoesExibicao"))
        verificadas += 1

    assert verificadas >= 1000, f"amostra pequena demais: {verificadas}"
    assert not divergencias, (
        f"{len(divergencias)} divergências em {verificadas} fichas "
        f"(primeiras 5): {divergencias[:5]}"
    )
