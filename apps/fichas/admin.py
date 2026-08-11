from django.contrib import admin

from apps.fichas.models import (
    Chave,
    Ficha,
    Ficha_Ingrediente,
    Ingrediente,
    Membro,
    Nutriente,
    Tabela,
)

admin.site.register(Ficha)
admin.site.register(Ingrediente)
admin.site.register(Tabela)
admin.site.register(Nutriente)
admin.site.register(Membro)
admin.site.register(Ficha_Ingrediente)
admin.site.register(Chave)
