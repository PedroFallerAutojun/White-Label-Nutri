"""Serviços de aplicação: ponte entre os models e o domínio puro.

Substitui o attTabela/att100gIngrediente do original com o mesmo resultado
(paridade garantida por tests/unit/test_paridade_calculo.py), mas em uma única
transação com um único save por entidade.
"""
from django.db import transaction

from apps.fichas.dominio.calculo import EntradaCalculo, ItemReceita, calcular
from apps.fichas.dominio.nutrientes import NUTRIENTES
from apps.fichas.models import Ficha, Ficha_Ingrediente, Tabela


def obter_tabela(ficha: Ficha) -> Tabela:
    """BR-015: a Tabela de uma Ficha tem o MESMO pk (convenção do banco legado).
    Cria se não existir (também sana fichas órfãs do backup — B4/S1)."""
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
        if chave in r.vd:  # acucaresTotais_VD nunca é recalculado (original)
            setattr(tabela, f"{chave}_VD", r.vd[chave])
    tabela.save()

    ficha.pesoLiquidoPreparacao = r.peso_liquido_preparacao
    ficha.numPorcoes = r.num_porcoes
    ficha.save()
    return tabela


def normalizar_100g(ingrediente) -> None:
    """BR-001: X_100g = X * 100 / qtdeDoIngrediente (None → 0). Não salva."""
    qtde = ingrediente.qtdeDoIngrediente or 0
    for n in NUTRIENTES:
        valor = getattr(ingrediente, n.chave)
        if valor is not None and qtde:
            setattr(ingrediente, f"{n.chave}_100g", (valor * 100) / qtde)
        else:
            setattr(ingrediente, f"{n.chave}_100g", 0)
