"""Arredondamento ANVISA (BR-006/BR-007).

Qualquer mudança aqui altera rótulos já emitidos aos clientes — não
"corrigir" sem decisão registrada em docs/REGRAS_DE_NEGOCIO.md.
"""
import math


def round_half_down(n: float, decimals: int = 0) -> float:
    """Arredonda para baixo na metade exata: 32,4→32 · 32,5→32 · 32,6→33."""
    multiplier = 10**decimals
    return math.ceil(n * multiplier - 0.5) / multiplier


def arredonda_anvisa(condicao_para_zero: bool, valor: float | None, unidade: str | None) -> float:
    """Regras de arredondamento da rotulagem (RDC 429/2020 / IN 75/2020).

    - condição de "declarável como zero" satisfeita → 0.0 (BR-007)
    - kcal/kJ → inteiro
    - valor ≥ 10 → inteiro; 1 ≤ valor < 10 → 1 casa
    - valor < 1 → 1 casa para g; 2 casas para mg/µg (e demais unidades)
    """
    if condicao_para_zero:
        return 0.0
    if valor is None:
        return 0.0

    unidade = (unidade or "").strip()

    if unidade in ("kcal", "kJ"):
        return round_half_down(valor, 0)
    if valor >= 10:
        return round_half_down(valor, 0)
    if valor >= 1:
        return round_half_down(valor, 1)
    if unidade == "g":
        return round_half_down(valor, 1)
    return round_half_down(valor, 2)
