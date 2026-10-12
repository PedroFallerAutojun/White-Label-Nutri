from django.contrib.postgres.operations import UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):
    """Busca sem acento nos filtros (apps/fichas/busca.py)."""

    dependencies = [
        ("fichas", "0001_initial"),
    ]

    operations = [
        UnaccentExtension(),
    ]
