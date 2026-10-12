"""Busca textual dos filtros: ignora acentos e maiúsculas, e cada palavra digitada
precisa aparecer no campo, em qualquer ordem ("acucar uniao" acha "Açúcar (União)").

Usa a extensão `unaccent` do PostgreSQL (migração 0002 de fichas)."""
from django.db.models import Q


def contem_palavras(campo: str, termo: str) -> Q:
    filtro = Q()
    for palavra in (termo or "").split():
        filtro &= Q(**{f"{campo}__unaccent__icontains": palavra})
    return filtro
