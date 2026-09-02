"""Testes do núcleo de domínio: arredondamento ANVISA e registro de nutrientes."""
import pytest

from apps.fichas.dominio.arredondamento import arredonda_anvisa, round_half_down
from apps.fichas.dominio.nutrientes import NUTRIENTES, ORDEM_ROTULO, POR_CHAVE


# --- BR-006: round_half_down -------------------------------------------------
@pytest.mark.parametrize(
    "valor,decimais,esperado",
    [
        (32.4, 0, 32), (32.5, 0, 32), (32.6, 0, 33),
        (1.25, 1, 1.2), (1.26, 1, 1.3), (1.15, 1, 1.1),
        (0.005, 2, 0.0), (0.006, 2, 0.01),
    ],
)
def test_round_half_down(valor, decimais, esperado):
    assert round_half_down(valor, decimais) == pytest.approx(esperado)


# --- BR-006/BR-007: faixas ANVISA -------------------------------------------
@pytest.mark.parametrize(
    "zero,valor,unidade,esperado",
    [
        (True, 123.4, "g", 0.0),          # condição de zero vence tudo
        (False, None, "g", 0.0),          # None → 0
        (False, 151.4, "kcal", 151),      # kcal → inteiro
        (False, 633.5, "kJ", 633),        # kJ → inteiro (half-down)
        (False, 12.66, "g", 13),          # ≥10 → inteiro
        (False, 9.96, "g", 10.0),         # 1..10 → 1 casa
        (False, 2.34, "mg", 2.3),
        (False, 0.55, "g", 0.5),          # <1 g → 1 casa (half-down: 0.55→0.5)
        (False, 0.056, "mg", 0.06),       # <1 mg → 2 casas
        (False, 0.056, "μg", 0.06),
        (False, 0.44, "", 0.44),          # unidade desconhecida → 2 casas
    ],
)
def test_arredonda_anvisa(zero, valor, unidade, esperado):
    assert arredonda_anvisa(zero, valor, unidade) == pytest.approx(esperado)


# --- Registro de nutrientes ---------------------------------------------------
def test_registro_tem_46_nutrientes():
    assert len(NUTRIENTES) == 46
    assert len(POR_CHAVE) == 46  # chaves únicas


def test_ordem_do_rotulo_continua_e_unica():
    ordens = [n.ordem_rotulo for n in ORDEM_ROTULO]
    assert ordens == list(range(1, 46))  # 45 linhas (kJ divide a linha com kcal)


def test_mostrar_padrao_reflete_obrigatorios_anvisa():
    visiveis = {n.chave for n in NUTRIENTES if n.mostrar_padrao}
    assert visiveis == {
        "proteinas", "gordTotais", "carboidratos", "fibras", "energiakcal",
        "energiaKJ", "sodio", "gordSat", "gordTrans", "acucaresadd",
        "acucaresTotais",
    }


def test_indentados_batem_com_original():
    indentados = {n.rotulo for n in NUTRIENTES if n.indentado}
    assert indentados == {
        "Açúcares totais", "Açúcares adicionados", "Gorduras Saturadas",
        "Gorduras Trans", "Gorduras monosaturadas", "Gorduras polissaturadas",
        "Colesterol",
    }
