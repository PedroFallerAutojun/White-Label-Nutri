from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

# Limite do arquivo de logotipo. Serve para não carregar imagens enormes em cada
# requisição e para manter a linha de configuração pequena.
TAMANHO_MAXIMO_LOGOTIPO = 1024 * 1024  # 1 MB
FORMATOS_LOGOTIPO = {
    "PNG": "image/png",
    "JPEG": "image/jpeg",
    "WEBP": "image/webp",
}


class ConfiguracaoInstancia(models.Model):
    """Configuração white-label desta instância (uma linha por banco).

    Cada empresa cliente roda com banco próprio; o que varia entre elas
    fica aqui: identidade visual e regras configuráveis.
    """

    nome_exibicao = models.CharField(
        "Nome da empresa", max_length=120, default="Nutri White-Label"
    )

    # O logotipo fica NO BANCO, não em arquivo. Plataformas como Heroku, Render e
    # Fly usam disco efêmero: um arquivo enviado pelo cliente desapareceria no
    # próximo restart. Como cada empresa tem banco próprio, guardar aqui faz a
    # identidade visual viajar junto com os dados e sobreviver a qualquer deploy.
    logotipo_dados = models.BinaryField(
        "Logotipo (conteúdo)", blank=True, null=True, editable=False
    )
    logotipo_tipo = models.CharField(
        "Logotipo (tipo)", max_length=40, blank=True, editable=False
    )
    logotipo_atualizado_em = models.DateTimeField(blank=True, null=True, editable=False)

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

    @property
    def tem_logotipo(self) -> bool:
        return bool(self.logotipo_dados)

    def definir_logotipo(self, conteudo: bytes, tipo: str) -> None:
        self.logotipo_dados = conteudo
        self.logotipo_tipo = tipo
        self.logotipo_atualizado_em = timezone.now()

    def remover_logotipo(self) -> None:
        self.logotipo_dados = None
        self.logotipo_tipo = ""
        self.logotipo_atualizado_em = None