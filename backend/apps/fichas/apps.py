from django.apps import AppConfig


class FichasConfig(AppConfig):
    name = "apps.fichas"
    # O label define os nomes das tabelas (fichas_*) e o registro de migrations
    # e content types no banco — não mudar em bases já existentes.
    label = "fichas"
    default_auto_field = "django.db.models.AutoField"
    verbose_name = "Fichas técnicas"
