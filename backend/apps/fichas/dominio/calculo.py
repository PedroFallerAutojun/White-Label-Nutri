"""Pipeline de cálculo da tabela nutricional (BR-001..BR-010).

Função pura, sem Django: recebe os pesos da ficha e os itens da receita e
devolve os valores totais, por 100 g, por porção, arredondados e o %VD.

Particularidades do pipeline, todas deliberadas (docs/REGRAS_DE_NEGOCIO.md):

- o valor por 100 g gravado é o ARREDONDADO — é ele que vai ao rótulo;
- a condição de zerar gorduras totais por porção usa o gordPoli total,
  enquanto a de 100 g usa gordPoli_100g;
- o %VD é calculado sobre o valor já arredondado;
- acucaresTotais_VD nunca é recalculado (a linha sai em branco no rótulo).

Mudanças aqui alteram rótulos já emitidos: leia BR-006/BR-008 antes e rode
tests/unit/test_paridade_calculo.py, que confere o pipeline contra 1.556 fichas
reais (docs/TESTES.md).
"""
from dataclasses import dataclass, field

from apps.fichas.dominio.arredondamento import arredonda_anvisa
from apps.fichas.dominio.nutrientes import NUTRIENTES

CHAVES = tuple(n.chave for n in NUTRIENTES)


@dataclass
class ItemReceita:
    peso_liquido: float
    ing_100g: dict[str, float]  # chave do nutriente -> valor por 100 g do ingrediente


@dataclass
class EntradaCalculo:
    peso_total: float | None
    peso_porcao: float | None
    peso_anvisa: float | None
    itens: list[ItemReceita]


@dataclass
class ResultadoCalculo:
    total: dict[str, float] = field(default_factory=dict)
    por_100g: dict[str, float] = field(default_factory=dict)
    por_porcao: dict[str, float] = field(default_factory=dict)
    arredondado: dict[str, float] = field(default_factory=dict)
    vd: dict[str, int] = field(default_factory=dict)      # sem acucaresTotais
    peso_liquido_preparacao: float = 0.0
    num_porcoes: int = 0


def calcular(
    entrada: EntradaCalculo, unidades: dict[str, str] | None = None
) -> ResultadoCalculo:
    """`unidades` permite arredondar com as unidades GRAVADAS na tabela
    (tabela.X_unidadeMd); sem override, usa os defaults do registro."""
    r = ResultadoCalculo()

    # BR-002 — soma da receita por peso líquido (energia fica de fora: BR-003)
    for chave in CHAVES:
        acumulado = 0.0
        if chave not in ("energiakcal", "energiaKJ"):
            for item in entrada.itens:
                peso = item.peso_liquido or 0
                acumulado += (item.ing_100g.get(chave) or 0) / 100 * peso
        r.total[chave] = acumulado

    # BR-003 — energia por Atwater
    r.total["energiakcal"] = (
        r.total["proteinas"] * 4 + r.total["carboidratos"] * 4 + r.total["gordTotais"] * 9
    )
    r.total["energiaKJ"] = r.total["energiakcal"] * 4.184

    # BR-004 — por 100 g da preparação (peso total INFORMADO)
    peso_total = entrada.peso_total
    for chave in CHAVES:
        if peso_total and peso_total > 0:
            r.por_100g[chave] = (r.total[chave] * 100) / peso_total
        else:
            r.por_100g[chave] = 0

    # BR-005 — por porção (peso ANVISA tem precedência)
    peso_porcao = entrada.peso_anvisa or entrada.peso_porcao or 0
    for chave in CHAVES:
        r.por_porcao[chave] = (r.por_100g[chave] / 100) * peso_porcao

    # BR-006/BR-007 — arredondamento com condições de zero. A ordem importa:
    # as condições leem por_100g/por_porcao ANTES de o por_100g ser reescrito.
    p = r.por_porcao
    c = r.por_100g

    def zera(chave, limite):
        return (p[chave] <= limite, c[chave] <= limite)

    condicoes: dict[str, tuple[bool, bool]] = {chave: (False, False) for chave in CHAVES}
    condicoes["proteinas"] = zera("proteinas", 0.5)
    condicoes["gordTotais"] = (
        p["gordTotais"] <= 0.5 and p["gordSat"] <= 0.5 and p["gordTrans"] <= 0.5
        and p["gordMono"] == 0 and r.total["gordPoli"] == 0,  # total, não por porção
        c["gordTotais"] <= 0.5 and c["gordSat"] <= 0.5 and c["gordTrans"] <= 0.5
        and c["gordMono"] == 0 and c["gordPoli"] == 0,
    )
    condicoes["carboidratos"] = zera("carboidratos", 0.5)
    condicoes["fibras"] = zera("fibras", 0.5)
    condicoes["energiakcal"] = zera("energiakcal", 4)
    condicoes["energiaKJ"] = zera("energiaKJ", 17)
    condicoes["sodio"] = zera("sodio", 5)
    condicoes["gordSat"] = zera("gordSat", 0.2)
    condicoes["gordTrans"] = zera("gordTrans", 0.2)

    unidade = {n.chave: n.unidade for n in NUTRIENTES}
    if unidades:
        unidade.update(unidades)
    for chave in CHAVES:
        cond_porcao, cond_100g = condicoes[chave]
        r.arredondado[chave] = arredonda_anvisa(cond_porcao, p[chave], unidade[chave])
        # o por 100 g gravado passa a ser o arredondado (BR-006)
        r.por_100g[chave] = arredonda_anvisa(cond_100g, c[chave], unidade[chave])

    # BR-010 — dados da ficha
    soma = 0.0
    for item in entrada.itens:
        soma += item.peso_liquido or 0
    r.peso_liquido_preparacao = soma
    if entrada.peso_porcao and entrada.peso_anvisa:
        r.num_porcoes = int(entrada.peso_porcao / entrada.peso_anvisa)
    else:
        r.num_porcoes = 0

    # BR-008 — %VD sobre o valor já arredondado
    for n in NUTRIENTES:
        if n.chave == "acucaresTotais":
            continue  # açúcares totais saem sem %VD no rótulo (BR-009)
        if n.vd_referencia is None:
            r.vd[n.chave] = 0
        else:
            r.vd[n.chave] = round((100 * r.arredondado[n.chave]) / n.vd_referencia)
    return r
