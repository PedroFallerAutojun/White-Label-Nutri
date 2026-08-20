"""Views da plataforma: servir a identidade visual da instância."""
from django.http import Http404, HttpResponse
from django.views.decorators.http import last_modified, require_GET

from apps.plataforma.models import ConfiguracaoInstancia


def _atualizado_em(request):
    configuracao = ConfiguracaoInstancia.atual()
    return configuracao.logotipo_atualizado_em if configuracao else None


@require_GET
@last_modified(_atualizado_em)
def logotipo_instancia(request):
    """Entrega o logotipo guardado no banco.

    É público de propósito: aparece na tela de login, antes de qualquer sessão.
    O cabeçalho Last-Modified evita rebaixar o conteúdo a cada requisição — o
    navegador revalida e recebe 304 enquanto o logotipo não mudar.
    """
    configuracao = ConfiguracaoInstancia.atual()
    if not configuracao or not configuracao.tem_logotipo:
        raise Http404("Esta instância não tem logotipo configurado.")

    resposta = HttpResponse(
        bytes(configuracao.logotipo_dados),
        content_type=configuracao.logotipo_tipo or "application/octet-stream",
    )
    resposta["Cache-Control"] = "public, max-age=300"
    return resposta