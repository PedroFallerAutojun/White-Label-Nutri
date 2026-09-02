from django.core.exceptions import ValidationError
from django.db import models


class ConfiguracaoInstancia(models.Model):
    """Configuração white-label desta instância (uma linha por banco).

    Cada empresa cliente roda com banco próprio; o que varia entre elas
    fica aqui: identidade visual e regras configuráveis.
    """

    nome_exibicao = models.CharField(
        "Nome da empresa", max_length=120, default="Nutri White-Label"
    )
    logotipo = models.ImageField(upload_to="branding/", blank=True, null=True)
    cor_primaria = models.CharField(
        "Cor primária (hex)", max_length=7, default="#198754"
    )
    ano_corte_ingredientes = models.PositiveIntegerField(
        "Ano de corte de ingredientes",
        blank=True,
        null=True,
        help_text=(
            "Se preenchido, as listas de ingredientes só exibem os criados a partir "
            "deste ano — útil para esconder cargas antigas da base (BR-017)."
        ),
    )
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Configuração da instância"
        verbose_name_plural = "Configuração da instância"

    def __str__(self):
        return f"Configuração: {self.nome_exibicao}"

    def clean(self):
        if not self.pk and ConfiguracaoInstancia.objects.exists():
            raise ValidationError("Já existe uma configuração para esta instância.")

    @classmethod
    def atual(cls):
        return cls.objects.first()
