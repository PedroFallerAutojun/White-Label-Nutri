from django import forms
from django.contrib import admin

from apps.plataforma.models import (
    FORMATOS_LOGOTIPO,
    TAMANHO_MAXIMO_LOGOTIPO,
    ConfiguracaoInstancia,
)


class ConfiguracaoInstanciaForm(forms.ModelForm):
    """O logotipo entra como arquivo e é guardado no banco (ver models)."""

    logotipo = forms.FileField(
        label="Logotipo",
        required=False,
        help_text=(
            "PNG, JPG ou WEBP, até 1 MB. Fica guardado no banco desta instância, "
            "então sobrevive a reinícios e novos deploys."
        ),
    )
    remover_logotipo = forms.BooleanField(
        label="Remover o logotipo atual", required=False
    )

    class Meta:
        model = ConfiguracaoInstancia
        fields = ["nome_exibicao", "cor_primaria", "ano_corte_ingredientes"]

    def clean_logotipo(self):
        arquivo = self.cleaned_data.get("logotipo")
        if not arquivo:
            return None

        if arquivo.size > TAMANHO_MAXIMO_LOGOTIPO:
            raise forms.ValidationError(
                f"O arquivo tem {arquivo.size // 1024} KB; o limite é "
                f"{TAMANHO_MAXIMO_LOGOTIPO // 1024} KB."
            )

        # Confirma que é mesmo uma imagem e descobre o formato real — a extensão
        # do arquivo não é confiável.
        from PIL import Image, UnidentifiedImageError

        arquivo.seek(0)
        try:
            imagem = Image.open(arquivo)
            imagem.verify()
        except (UnidentifiedImageError, OSError):
            raise forms.ValidationError("O arquivo não é uma imagem válida.")

        if imagem.format not in FORMATOS_LOGOTIPO:
            formatos = ", ".join(sorted(FORMATOS_LOGOTIPO))
            raise forms.ValidationError(
                f"Formato {imagem.format} não aceito. Use um destes: {formatos}."
            )

        arquivo.seek(0)
        self._conteudo_logotipo = arquivo.read()
        self._tipo_logotipo = FORMATOS_LOGOTIPO[imagem.format]
        return arquivo

    def save(self, commit=True):
        configuracao = super().save(commit=False)
        if self.cleaned_data.get("remover_logotipo"):
            configuracao.remover_logotipo()
        elif self.cleaned_data.get("logotipo"):
            configuracao.definir_logotipo(self._conteudo_logotipo, self._tipo_logotipo)
        if commit:
            configuracao.save()
        return configuracao


@admin.register(ConfiguracaoInstancia)
class ConfiguracaoInstanciaAdmin(admin.ModelAdmin):
    form = ConfiguracaoInstanciaForm
    list_display = ("nome_exibicao", "cor_primaria", "ano_corte_ingredientes", "tem_logotipo")
    readonly_fields = ("previa_do_logotipo",)
    fields = (
        "nome_exibicao",
        "cor_primaria",
        "ano_corte_ingredientes",
        "previa_do_logotipo",
        "logotipo",
        "remover_logotipo",
    )

    @admin.display(description="Logotipo atual")
    def previa_do_logotipo(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html

        if not obj or not obj.tem_logotipo:
            return "nenhum logotipo enviado"
        return format_html(
            '<img src="{}" alt="Logotipo atual" style="max-height:60px;'
            'background:#eee;padding:4px;border-radius:4px">',
            reverse("logotipoInstancia"),
        )

    @admin.display(boolean=True, description="Tem logotipo")
    def tem_logotipo(self, obj):
        return obj.tem_logotipo

    def has_add_permission(self, request):
        return not ConfiguracaoInstancia.objects.exists()