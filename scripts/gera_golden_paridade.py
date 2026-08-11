"""Gera o golden de paridade de cálculo e de montagem do rótulo.

Para cada ficha com tabela, captura:
- entradas: pesos da ficha + itens da receita (na ordem do queryset) com os
  valores _100g dos ingredientes;
- tabela_persistida: os 46 nutrientes × (total, _100g, _Porcao, _Arred, _VD,
  _Mostrar, _unidadeMd) como estão gravados + informações complementares;
- recalculo: os mesmos campos APÓS rodar o attTabela original (transação
  revertida — o banco não muda) + pesoLiquidoPreparacao e numPorcoes.

Uso: manage.py shell < este arquivo (cwd = Nutri_Jr, banco = cópia restaurada).
"""
import gzip
import json

from django.db import transaction

from fichas.models import Ficha, Ficha_Ingrediente, Nutriente, Tabela
from fichas.views import attTabela

CHAVES = [
    "proteinas", "gordTotais", "carboidratos", "fibras", "energiakcal", "energiaKJ",
    "calcio", "ferro", "magnesio", "fosforo", "potassio", "sodio", "zinco", "cobre",
    "manganes", "retinol", "RE", "vitaminaARAE", "vitaminaC", "tiamina", "riboflavina",
    "niancina", "piridoxina", "gordSat", "gordTrans", "gordPoli", "gordMono",
    "colesterol", "acucaresadd", "omega6", "omega3", "vitaminaD", "vitaminaE",
    "vitaminaK", "biotina", "acidoFolico", "acidoPantotenico", "vitaminaB12",
    "cloreto", "cromo", "fluor", "iodo", "molibdenio", "selenio", "colina",
    "acucaresTotais",
]


def snapshot_tabela(t):
    dados = {}
    for chave in CHAVES:
        dados[chave] = [
            getattr(t, chave),
            getattr(t, f"{chave}_100g"),
            getattr(t, f"{chave}_Porcao"),
            getattr(t, f"{chave}_Arred"),
            getattr(t, f"{chave}_VD"),
            getattr(t, f"{chave}_Mostrar"),
            getattr(t, f"{chave}_unidadeMd"),
        ]
    return dados


class Rollback(Exception):
    pass


saida = {}
pks = list(Ficha.objects.filter(tabela__isnull=False).order_by("id").values_list("id", flat=True))
for pk in pks:
    ficha = Ficha.objects.get(pk=pk)
    tabela = Tabela.objects.get(pk=pk)
    itens_qs = Ficha_Ingrediente.objects.filter(ficha=ficha)
    itens = [
        {
            "pesoLiquido": item.pesoLiquido,
            "pesoBruto": item.pesoBruto,
            "nomeFantasia": item.nomeFantasia,
            "medidaCaseira": item.medidaCaseira,
            "composicao": item.ingrediente.composicao,
            "ing_100g": {c: getattr(item.ingrediente, f"{c}_100g") for c in CHAVES},
        }
        for item in itens_qs
    ]
    extras = [
        [n.nomeNutri, n.qtde, n.qtde_Arred, n.qtde_VD, n.medida]
        for n in Nutriente.objects.filter(origemTabela=tabela)
    ]
    registro = {
        "entradas": {
            "pesoTotal": ficha.pesoTotal,
            "pesoPorcao": ficha.pesoPorcao,
            "pesoAnvisa": ficha.pesoAnvisa,
            "itens": itens,
        },
        "tabela_persistida": snapshot_tabela(tabela),
        "informacoesComplementares": tabela.informacoesComplementares,
        "extras": extras,
    }
    try:
        with transaction.atomic():
            try:
                attTabela(tabela, itens_qs, ficha)
            except Exception as e:
                registro["recalculo_erro"] = f"{type(e).__name__}: {e}"
                raise Rollback
            tabela.refresh_from_db()
            ficha.refresh_from_db()
            registro["recalculo"] = snapshot_tabela(tabela)
            registro["recalculo_ficha"] = {
                "pesoLiquidoPreparacao": ficha.pesoLiquidoPreparacao,
                "numPorcoes": ficha.numPorcoes,
            }
            raise Rollback
    except Rollback:
        pass
    saida[pk] = registro

caminho = "/tmp/claude-0/-home-user/3aab228f-52e9-50b4-b140-a71a356e09b8/scratchpad/golden_paridade.json.gz"
with gzip.open(caminho, "wt", encoding="utf-8") as f:
    json.dump({"origem": "attTabela original sobre BackupNutriJR 2026-06-18", "fichas": saida}, f)
print("fichas capturadas:", len(saida))
