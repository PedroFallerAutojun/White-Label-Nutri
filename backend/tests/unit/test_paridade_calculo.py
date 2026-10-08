"""Paridade do pipeline de cálculo (D-008): dominio.calculo.calcular deve
reproduzir o attTabela original em TODAS as fichas do backup (oráculo
golden_paridade.json.gz, gerado pelo código original — 1.556 fichas com
recálculo bem-sucedido; 2 fichas com dados nulos crasham o próprio original).
"""
import gzip
import json
import math
from pathlib import Path

import pytest

from apps.fichas.dominio.calculo import EntradaCalculo, ItemReceita, calcular
from apps.fichas.dominio.nutrientes import NUTRIENTES

GOLDEN = Path(__file__).resolve().parent.parent / "golden" / "golden_paridade.json.gz"


@pytest.fixture(scope="module")
def golden():
    with gzip.open(GOLDEN, "rt", encoding="utf-8") as f:
        return json.load(f)["fichas"]


def _quase_igual(a, b):
    a = a or 0
    b = b or 0
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)


def test_paridade_calculo_completa(golden):
    """Compara total, por 100 g, por porção, arredondado e %VD dos 46 nutrientes."""
    fichas_ok = {pk: g for pk, g in golden.items() if "recalculo" in g}
    assert len(fichas_ok) >= 1556

    divergencias = []
    for pk, g in fichas_ok.items():
        ent = g["entradas"]
        entrada = EntradaCalculo(
            peso_total=ent["pesoTotal"],
            peso_porcao=ent["pesoPorcao"],
            peso_anvisa=ent["pesoAnvisa"],
            itens=[
                ItemReceita(peso_liquido=i["pesoLiquido"], ing_100g=i["ing_100g"])
                for i in ent["itens"]
            ],
        )
        unidades = {chave: valores[6] for chave, valores in g["tabela_persistida"].items()}
        r = calcular(entrada, unidades=unidades)

        esperado = g["recalculo"]
        for n in NUTRIENTES:
            chave = n.chave
            exp = esperado[chave]  # [total, _100g, _Porcao, _Arred, _VD, ...]
            checks = [
                ("total", r.total[chave], exp[0]),
                ("100g", r.por_100g[chave], exp[1]),
                ("porcao", r.por_porcao[chave], exp[2]),
                ("arred", r.arredondado[chave], exp[3]),
            ]
            for nome, meu, dele in checks:
                if not _quase_igual(meu, dele):
                    divergencias.append((pk, chave, nome, meu, dele))
            if chave != "acucaresTotais" and r.vd[chave] != (exp[4] or 0):
                divergencias.append((pk, chave, "vd", r.vd[chave], exp[4]))

        rf = g["recalculo_ficha"]
        if not _quase_igual(r.peso_liquido_preparacao, rf["pesoLiquidoPreparacao"]):
            divergencias.append((pk, "-", "pesoLiquidoPreparacao",
                                 r.peso_liquido_preparacao, rf["pesoLiquidoPreparacao"]))
        if r.num_porcoes != (rf["numPorcoes"] or 0):
            divergencias.append((pk, "-", "numPorcoes", r.num_porcoes, rf["numPorcoes"]))

    assert not divergencias, (
        f"{len(divergencias)} divergências (primeiras 10): {divergencias[:10]}"
    )
