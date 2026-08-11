from apps.plataforma.models import ConfiguracaoInstancia


def instancia(request):
    """Disponibiliza o branding da instância em todos os templates (D-011)."""
    config = ConfiguracaoInstancia.atual()
    return {
        "instancia_nome": config.nome_exibicao if config else "Nutri White-Label",
        "instancia_logotipo": config.logotipo if config and config.logotipo else None,
        "instancia_cor": config.cor_primaria if config else "#198754",
    }
