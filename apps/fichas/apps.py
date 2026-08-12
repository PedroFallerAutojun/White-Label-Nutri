from django.apps import AppConfig


class FichasConfig(AppConfig):
    name = "apps.fichas"
    # Label preservado do sistema original: o banco legado registra migrations e
    # content types sob "fichas" (D-012).
    label = "fichas"
    default_auto_field = "django.db.models.AutoField"
    verbose_name = "Fichas técnicas"
