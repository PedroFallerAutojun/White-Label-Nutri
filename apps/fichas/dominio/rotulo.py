"""Montagem do rótulo ANVISA (BR-009..BR-014, BR-030) — porta fiel da fichaX.

Diferenças INTENCIONAIS em relação ao original (D-005, registradas):
- B2 corrigido: Biotina usa biotina_Arred (o original crashava com Biotina_Arred);
- B3 corrigido: a coluna "por 100 g" do Manganês usa manganes_100g
  (o original mostrava magnesio_100g);
- B15 corrigido: pesos de porção ausentes não crasham (retorna 0).

Todo o resto reproduz o original à risca — validado por
tests/integration/test_paridade_rotulo.py contra o golden de 1.557 fichas.
"""
from dataclasses import dataclass

from apps.fichas.dominio.nutrientes import ORDEM_ROTULO

# BR-030 — linhas exibidas com recuo
INDENTADOS = [
    "Açúcares totais", "Açúcares adicionados", "Gorduras Saturadas",
    "Gorduras Trans", "Gorduras monosaturadas", "Gorduras polissaturadas",
    "Colesterol",
]


def tira_zero(valor):
    """BR-013: inteiro sem ',0'; decimal com vírgula."""
    if valor is None:
        return valor
    if valor == int(valor):
        return int(valor)
    return str(valor).replace(".", ",")


def calcular_num_porcoes(peso_porcao, peso_anvisa) -> str:
    """BR-011: '10 porções' | 'Cerca de 7 porções' | '1 e 1/2 porções' | '3/4 porção'."""
    if not peso_porcao or not peso_anvisa:
        return "0 porções"

    porcoes = peso_porcao / peso_anvisa

    def plural_com_contagem(valor):
        inteiro = round(valor)
        return f"{inteiro} {'porção' if inteiro == 1 else 'porções'}"

    if abs(porcoes - round(porcoes)) < 0.001:
        return plural_com_contagem(porcoes)
    if porcoes > 3:
        return f"Cerca de {plural_com_contagem(porcoes)}"

    quartos = round(porcoes * 4)
    inteiro, resto = divmod(quartos, 4)
    fracoes = {1: "1/4", 2: "1/2", 3: "3/4"}
    if resto == 0:
        return plural_com_contagem(inteiro)
    if inteiro == 0:
        return f"{fracoes[resto]} porção"
    return f"{inteiro} e {fracoes[resto]} porções"


def peso_anvisa_sem_zero(peso_anvisa, peso_porcao):
    """Peso da porção exibido no cabeçalho (B15 corrigido: ausente → 0)."""
    peso = peso_anvisa or peso_porcao
    return tira_zero(int(peso)) if peso else 0


def num_porcoes_exibicao(peso_porcao, peso_anvisa) -> int:
    """BR-010 recalculado na exibição (fichas antigas têm valor defasado gravado)."""
    if peso_porcao and peso_anvisa:
        return int(peso_porcao / peso_anvisa)
    return 0


def nutrientes_altos(acucaresadd_100g, gord_sat_100g, sodio_100g) -> list[str]:
    """BR-012 — limiares de 'ALTO EM' para alimentos sólidos (RDC 429/2020)."""
    altos = []
    if (acucaresadd_100g or 0) >= 15:
        altos.append("acucares")
    if (gord_sat_100g or 0) >= 6:
        altos.append("gorduras_saturadas")
    if (sodio_100g or 0) >= 600:
        altos.append("sodio")
    return altos


def combinacao_lupa(altos: list[str]) -> str | None:
    """Nome canônico da combinação de lupas (None = sem lupa)."""
    a = "acucares" in altos
    g = "gorduras_saturadas" in altos
    s = "sodio" in altos
    if a and g and s:
        return "acucares+gorduras+sodio"
    if a and g:
        return "acucares+gorduras"
    if a and s:
        return "acucares+sodio"
    if g and s:
        return "gorduras+sodio"
    if a:
        return "acucares"
    if g:
        return "gorduras"
    if s:
        return "sodio"
    return None


@dataclass
class ValoresNutriente:
    arred: float
    vd: int | None
    unidade: str
    por_100g: float
    mostrar: bool


def montar_linhas(
    valores: dict[str, ValoresNutriente],
    extras: list[tuple[str, float, int | None]] | None = None,
) -> list[list]:
    """Linhas da tabela final na ordem/formato exatos do original.

    Formato: [rótulo, valor porção formatado, %VD, unidade, valor 100 g formatado];
    linhas de nutrientes extras têm 3 posições: [nome, quantidade, %VD].
    """
    linhas: list[list] = []
    vd_trans = 0  # BR-009: gorduras trans sem %VD

    kcal = valores.get("energiakcal")
    kj = valores.get("energiaKJ")
    if kcal and kj and kcal.mostrar and kj.mostrar:
        linhas.append(
            ["Valor energético", str(tira_zero(kcal.arred)), kcal.vd,
             kcal.unidade, round(kcal.por_100g)]
        )

    for n in ORDEM_ROTULO:
        if n.chave == "energiakcal":
            continue  # já tratada acima (linha conjunta kcal/kJ)
        v = valores.get(n.chave)
        if not v or not v.mostrar:
            continue
        if n.vd_em_branco:
            vd = ""  # BR-009: açúcares totais sem VDR definido
        elif n.chave == "gordTrans":
            vd = vd_trans
        else:
            vd = v.vd
        linhas.append([n.rotulo, tira_zero(v.arred), vd, v.unidade, round(v.por_100g, 1)])

    for nome, qtde_arred, qtde_vd in extras or []:
        linhas.append([nome, tira_zero(qtde_arred), qtde_vd])

    # BR-013: coluna "por 100 g" recebe a mesma limpeza (inteiro sem ',0')
    for linha in linhas:
        if len(linha) > 4:
            linha[4] = tira_zero(linha[4])
    return linhas


def ordenar_ingredientes(itens: list[dict]) -> str:
    """BR-014: nomes fantasia por peso líquido decrescente, com composição."""
    ordenados = sorted(itens, key=lambda item: -(item.get("pesoLiquido") or 0))
    partes = []
    for item in ordenados:
        composicao = item.get("composicao")
        if composicao:
            partes.append(f"{item['nomeFantasia']} ({composicao})")
        else:
            partes.append(f"{item['nomeFantasia']}")
    texto = ", ".join(partes) + "."
    return texto.capitalize()
