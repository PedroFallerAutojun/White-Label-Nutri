"""Gera golden dataset de paridade: captura o contexto que a view fichaX do sistema
ORIGINAL envia ao template, para todas as fichas, rodando sobre a cópia do backup.
Uso: manage.py shell < este arquivo (cwd = Nutri_Jr)
"""
import json, gzip, hashlib, traceback
from django.conf import settings
settings.ALLOWED_HOSTS = ['*']

from django.test import RequestFactory
from django.contrib.auth.models import User
import fichas.views as v
from fichas.models import Ficha

capturado = {}
_render_original = v.render
def render_espiao(request, template, context=None):
    capturado['ctx'] = context
    return _render_original(request, template, context)
v.render = render_espiao

rf = RequestFactory()
user = User.objects.filter(username='admin').first()

def lupa_id(b64):
    if not b64:
        return None
    return hashlib.sha1(b64.encode()).hexdigest()[:12]

golden = {}
erros = {}
for ficha in Ficha.objects.order_by('id'):
    req = rf.get(f'/fichaX/{ficha.pk}')
    req.user = user
    capturado.clear()
    try:
        v.fichaX(req, ficha.pk)
        ctx = capturado['ctx']
        golden[ficha.pk] = {
            'nomeFicha': ficha.nomeFicha,
            'cliente': ficha.cliente,
            'finalizada': ficha.finalizada,
            'pesoAnvisaSemZero': ctx['pesoAnvisaSemZero'],
            'numPorcoesExibicao': ctx['numPorcoesExibicao'],
            'numPorcoes': ctx['fichaAtual'].numPorcoes,
            'medCaseiraPorcao': ficha.medCaseiraPorcao,
            'ordemIngredientes': ctx['ordemIngredientesFront'],
            'lupa': lupa_id(ctx['lupa_img']),
            'infComplementares': ctx['tabelaAtual'].informacoesComplementares,
            'linhas': ctx['nutrientesFinais'],
        }
    except Exception as e:
        erros[ficha.pk] = f"{type(e).__name__}: {e}"

# mapa das lupas: hash -> combinação
mapa_lupas = {}
import itertools
for combo in itertools.product([0, 1], repeat=3):
    ac, go, so = combo
    # reproduz a seleção de imagem da view
    if ac and go and so: nome = 'acucar+gordura+sodio'
    elif ac and go: nome = 'acucar+gordura'
    elif ac and so: nome = 'acucar+sodio'
    elif go and so: nome = 'gordura+sodio'
    elif ac: nome = 'acucar'
    elif go: nome = 'gordura'
    elif so: nome = 'sodio'
    else: continue
    mapa_lupas[nome] = None  # hashes preenchidos abaixo por inspeção do código

saida = {
    'origem': 'BackupNutriJR 2026-06-18 + código original Nutri_Jr',
    'total_fichas': Ficha.objects.count(),
    'geradas': len(golden),
    'erros': erros,
    'fichas': golden,
}
with gzip.open('/tmp/claude-0/-home-user/3aab228f-52e9-50b4-b140-a71a356e09b8/scratchpad/golden_fichax.json.gz', 'wt', encoding='utf-8') as f:
    json.dump(saida, f, ensure_ascii=False, default=str)
print(f"golden gerado: {len(golden)} fichas ok, {len(erros)} com erro")
tipos = {}
for e in erros.values():
    tipos[e.split(':')[0]] = tipos.get(e.split(':')[0], 0) + 1
print("erros por tipo:", tipos)
print("exemplos de erro:", dict(list(erros.items())[:5]))
