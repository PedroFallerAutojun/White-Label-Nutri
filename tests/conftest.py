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

    O nome original é restaurado antes do teardown do pytest-django — sem isso,
    a rotina de destruição do banco de teste apagaria a cópia do backup
    (D-002: a cópia é insumo de validação e nunca deve ser destruída).
    """
    banco = os.environ.get("PARIDADE_DB")
    if not banco:
        yield
        return

    from django.db import connections

    originais = {}
    for conexao in connections.all():
        originais[conexao.alias] = conexao.settings_dict["NAME"]
        conexao.close()
        conexao.settings_dict["NAME"] = banco
    try:
        yield
    finally:
        for conexao in connections.all():
            conexao.close()
            conexao.settings_dict["NAME"] = originais.get(
                conexao.alias, conexao.settings_dict["NAME"]
            )
