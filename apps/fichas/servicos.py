"""Serviços de aplicação: ponte entre os models e o domínio puro.

Lê a ficha e sua receita, chama o cálculo (apps/fichas/dominio/calculo.py) e
grava o resultado na Tabela — tudo em uma transação, com um save por entidade.
"""
import math

from django.db import transaction

from apps.fichas.dominio.calculo import EntradaCalculo, ItemReceita, calcular
from apps.fichas.dominio.nutrientes import NUTRIENTES
from apps.fichas.models import Ficha, Ficha_Ingrediente, Tabela


def obter_tabela(ficha: Ficha) -> Tabela:
    """BR-015: a Tabela de uma Ficha tem o MESMO pk. Cria se não existir."""
    try:
        return Tabela.objects.get(pk=ficha.pk)
    except Tabela.DoesNotExist:
        return Tabela.objects.create(pk=ficha.pk, origem=ficha)


@transaction.atomic
def recalcular_tabela(ficha: Ficha) -> Tabela:
    """Recalcula e persiste a tabela nutricional da ficha (BR-001..BR-010)."""
    tabela = obter_tabela(ficha)
    itens = Ficha_Ingrediente.objects.filter(ficha=ficha).select_related("ingrediente")

    entrada = EntradaCalculo(
        peso_total=ficha.pesoTotal,
        peso_porcao=ficha.pesoPorcao,
        peso_anvisa=ficha.pesoAnvisa,
        itens=[
            ItemReceita(
                peso_liquido=item.pesoLiquido,
                ing_100g={
                    n.chave: getattr(item.ingrediente, f"{n.chave}_100g")
                    for n in NUTRIENTES
                },
            )
            for item in itens
        ],
    )
    unidades = {n.chave: getattr(tabela, f"{n.chave}_unidadeMd") for n in NUTRIENTES}
    r = calcular(entrada, unidades=unidades)

    for n in NUTRIENTES:
        chave = n.chave
        setattr(tabela, chave, r.total[chave])
        setattr(tabela, f"{chave}_100g", r.por_100g[chave])
        setattr(tabela, f"{chave}_Porcao", r.por_porcao[chave])
        setattr(tabela, f"{chave}_Arred", r.arredondado[chave])
        if chave in r.vd:  # acucaresTotais_VD nunca é recalculado (BR-009)
            setattr(tabela, f"{chave}_VD", r.vd[chave])
    tabela.save()

    ficha.pesoLiquidoPreparacao = r.peso_liquido_preparacao
    ficha.numPorcoes = r.num_porcoes
    ficha.save()
    return tabela


def peso_porcao_efetivo(ficha) -> float:
    """BR-005: o peso ANVISA tem precedencia; o peso cliente e o fallback."""
    return ficha.pesoAnvisa or ficha.pesoPorcao or 0


def peso_porcao_implicito(ficha, tabela) -> float | None:
    """Peso de porcao que gerou as colunas GRAVADAS na tabela.

    Deduzido do valor energetico, que e guardado sem arredondamento:
        Porcao = total * peso / pesoTotal  =>  peso = Porcao * pesoTotal / total
    Retorna None quando nao ha como deduzir (receita vazia ou peso total zerado).
    """
    total = tabela.energiakcal or 0
    if not total or not ficha.pesoTotal:
        return None
    return (tabela.energiakcal_Porcao or 0) * ficha.pesoTotal / total


def conferir_tabela(ficha, tabela) -> dict:
    """Compara o que esta gravado com o que o calculo atual produziria.

    Nao grava nada. Serve para avisar quando um rotulo esta desatualizado — o
    caso mais grave e a coluna da porcao ter sido calculada com um peso diferente
    do que o rotulo declara, o que deixa o documento internamente incoerente.
    """
    itens = Ficha_Ingrediente.objects.filter(ficha=ficha).select_related("ingrediente")
    entrada = EntradaCalculo(
        peso_total=ficha.pesoTotal,
        peso_porcao=ficha.pesoPorcao,
        peso_anvisa=ficha.pesoAnvisa,
        itens=[
            ItemReceita(
                peso_liquido=item.pesoLiquido,
                ing_100g={n.chave: getattr(item.ingrediente, f"{n.chave}_100g") for n in NUTRIENTES},
            )
            for item in itens
        ],
    )
    unidades = {n.chave: getattr(tabela, f"{n.chave}_unidadeMd") for n in NUTRIENTES}
    esperado = calcular(entrada, unidades=unidades)

    divergencias = []
    for n in NUTRIENTES:
        if not getattr(tabela, f"{n.chave}_Mostrar"):
            continue  # so interessa o que aparece no rotulo
        gravado = getattr(tabela, f"{n.chave}_Arred") or 0
        novo = esperado.arredondado[n.chave] or 0
        if not math.isclose(gravado, novo, rel_tol=1e-6, abs_tol=1e-6):
            divergencias.append(
                {"rotulo": n.rotulo or n.chave, "gravado": gravado, "esperado": novo,
                 "unidade": n.unidade}
            )

    peso_declarado = peso_porcao_efetivo(ficha)
    peso_usado = peso_porcao_implicito(ficha, tabela)
    porcao_incoerente = bool(
        peso_declarado and peso_usado is not None
        and not math.isclose(peso_usado, peso_declarado, rel_tol=1e-3, abs_tol=0.05)
    )

    return {
        "desatualizada": bool(divergencias) or porcao_incoerente,
        "porcao_incoerente": porcao_incoerente,
        "peso_declarado": peso_declarado,
        "peso_usado": peso_usado,
        "divergencias": divergencias,
    }


def normalizar_100g(ingrediente) -> None:
    """BR-001: X_100g = X * 100 / qtdeDoIngrediente (None → 0). Não salva."""
    qtde = ingrediente.qtdeDoIngrediente or 0
    for n in NUTRIENTES:
        valor = getattr(ingrediente, n.chave)
        if valor is not None and qtde:
            setattr(ingrediente, f"{n.chave}_100g", (valor * 100) / qtde)
        else:
            setattr(ingrediente, f"{n.chave}_100g", 0)
