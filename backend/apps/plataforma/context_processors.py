from django.urls import reverse

from apps.plataforma.models import ConfiguracaoInstancia


def instancia(request):
    """Disponibiliza o branding da instância em todos os templates (D-011)."""
    config = ConfiguracaoInstancia.atual()
    tem_logotipo = bool(config and config.tem_logotipo)
    return {
        "instancia_nome": config.nome_exibicao if config else "Nutri White-Label",
        # O logotipo é servido por uma rota própria (fica no banco, não em arquivo).
        # O parâmetro de versão troca quando o logotipo muda, furando o cache do
        # navegador na hora certa. Em microssegundos: com segundos, uma troca logo
        # após a anterior manteria o mesmo endereço e o cliente veria a marca antiga.
        "instancia_logotipo_url": (
            f"{reverse('logotipoInstancia')}"
            f"?v={int(config.logotipo_atualizado_em.timestamp() * 1_000_000)}"
            if tem_logotipo and config.logotipo_atualizado_em
            else (reverse("logotipoInstancia") if tem_logotipo else None)
        ),
        "instancia_cor": config.cor_primaria if config else "#198754",
    }