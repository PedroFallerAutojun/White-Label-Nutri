from django.apps import AppConfig


class PlataformaConfig(AppConfig):
    name = "apps.plataforma"
    label = "plataforma"
    default_auto_field = "django.db.models.AutoField"
    verbose_name = "Plataforma (instância white-label)"

    def ready(self):
        # Registra as verificações da instância (manage.py check e deploy).
        from apps.plataforma import checks  # noqa: F401
