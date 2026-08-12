from django.contrib import admin

from apps.plataforma.models import ConfiguracaoInstancia


@admin.register(ConfiguracaoInstancia)
class ConfiguracaoInstanciaAdmin(admin.ModelAdmin):
    list_display = ("nome_exibicao", "cor_primaria", "ano_corte_ingredientes")

    def has_add_permission(self, request):
        return not ConfiguracaoInstancia.objects.exists()
