"""Configuração compartilhada dos testes.

Os testes de paridade ponta a ponta precisam do acervo legado (banco restaurado
do BackupNutriJR). Defina PARIDADE_DB para apontar o pytest a essa cópia:

    PARIDADE_DB=nutri_paridade pytest tests/integration/test_paridade_rotulo_e2e.py

Sem a variável, o pytest usa o banco de teste normal e o teste e2e é pulado.
"""
import os

import pytest


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Aponta a sessão de testes para a cópia do backup, quando solicitado.

    Não cria nem destrói o banco indicado — ele é uma cópia restaurada e os
    testes que o usam são somente leitura.
    """
    banco = os.environ.get("PARIDADE_DB")
    if banco:
        from django.db import connections

        for conexao in connections.all():
            conexao.close()
            conexao.settings_dict["NAME"] = banco
    yield
