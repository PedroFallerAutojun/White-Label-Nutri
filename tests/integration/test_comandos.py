"""Testes dos comandos de saneamento e provisionamento de instância (E6)."""
from io import StringIO

import pytest
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.management import CommandError, call_command

from apps.fichas.models import Chave, Ficha, Membro, Tabela
from apps.plataforma.models import ConfiguracaoInstancia


def executar(comando, *args, **kwargs):
    saida = StringIO()
    call_command(comando, *args, stdout=saida, stderr=saida, **kwargs)
    return saida.getvalue()


@pytest.fixture
def membro(db):
    user = User.objects.create_user("admin", password="s3nh4-forte")
    return Membro.objects.create(usuario=user, nome="Admin", semestre="", email="a@x.com")


@pytest.fixture
def acervo_legado(membro):
    """Simula o estado do backup: fichas órfãs, data suspeita e ficha sem pesos."""
    orfas = [
        Ficha.objects.create(
            autor=membro, cliente="C", nomeFicha=f"Órfã {i}", dataCriacao="2021-01-01",
            pesoTotal=100, pesoPorcao=50, pesoAnvisa=50,
        )
        for i in range(3)
    ]
    antiga = Ficha.objects.create(
        autor=membro, cliente="C", nomeFicha="Data errada", dataCriacao="2000-05-05",
        pesoTotal=100, pesoPorcao=50, pesoAnvisa=50,
    )
    Tabela.objects.create(pk=antiga.pk, origem=antiga)
    sem_pesos = Ficha.objects.create(
        autor=membro, cliente="C", nomeFicha="Sem pesos", dataCriacao="2022-01-01",
        pesoPorcao=None, pesoAnvisa=None,
    )
    Tabela.objects.create(pk=sem_pesos.pk, origem=sem_pesos)
    return {"orfas": orfas, "antiga": antiga, "sem_pesos": sem_pesos}


# ------------------------------------------------------------- sanear_backup


def test_saneamento_cria_tabelas_das_fichas_orfas(acervo_legado):
    """S1 — as 16 fichas órfãs do backup passam a abrir normalmente."""
    saida = executar("sanear_backup")
    assert "S1 criando tabela para 3 ficha(s) órfã(s)" in saida
    for ficha in acervo_legado["orfas"]:
        tabela = Tabela.objects.get(pk=ficha.pk)
        assert tabela.origem_id == ficha.pk  # BR-015 preservada


def test_saneamento_e_idempotente(acervo_legado):
    executar("sanear_backup")
    total_tabelas = Tabela.objects.count()
    total_config = ConfiguracaoInstancia.objects.count()

    saida = executar("sanear_backup")
    assert "S1 tabelas faltantes: nada a fazer" in saida
    assert "S7 configuração já existe" in saida
    assert Tabela.objects.count() == total_tabelas
    assert ConfiguracaoInstancia.objects.count() == total_config


def test_dry_run_nao_grava_nada(acervo_legado):
    saida = executar("sanear_backup", "--dry-run")
    assert "MODO SIMULAÇÃO" in saida
    assert not Tabela.objects.filter(pk=acervo_legado["orfas"][0].pk).exists()
    assert not ConfiguracaoInstancia.objects.exists()


def test_saneamento_configura_instancia_nutri_jr(acervo_legado):
    """S7 + D-010 — corte de ingredientes preservado como configuração."""
    executar("sanear_backup")
    config = ConfiguracaoInstancia.atual()
    assert config.nome_exibicao == "Nutri Jr"
    assert config.ano_corte_ingredientes == 2024


def test_saneamento_promove_admin_ao_grupo(acervo_legado):
    """S2 — o usuário admin do backup recebe o papel; sem hardcode de username."""
    saida = executar("sanear_backup")
    assert "virou administrador" in saida
    usuario = User.objects.get(username="admin")
    assert usuario.groups.filter(name=settings.GRUPO_ADMINISTRADORES).exists()


def test_saneamento_relata_dados_suspeitos_sem_alterar(acervo_legado):
    """S3/S4 — apenas sinaliza; nunca corrige dados do cliente."""
    saida = executar("sanear_backup")
    assert "data anterior a 2019" in saida
    assert "sem peso de porção" in saida
    acervo_legado["antiga"].refresh_from_db()
    assert acervo_legado["antiga"].dataCriacao.year == 2000  # intacta


def test_saneamento_nao_recalcula_tabelas_existentes(acervo_legado):
    """D-007 — os valores gravados são os rótulos já emitidos."""
    tabela = Tabela.objects.get(pk=acervo_legado["antiga"].pk)
    tabela.proteinas_Arred = 42.0
    tabela.save()
    executar("sanear_backup")
    tabela.refresh_from_db()
    assert tabela.proteinas_Arred == 42.0


def test_saneamento_avisa_quando_nao_ha_chave(acervo_legado):
    saida = executar("sanear_backup")
    assert "nenhuma chave de cadastro definida" in saida


# -------------------------------------------------------- bootstrap_instancia


def test_bootstrap_configura_empresa_nova(db):
    saida = executar(
        "bootstrap_instancia",
        "--nome", "Nutri Acme",
        "--admin", "ana",
        "--email", "ana@acme.com",
        "--senha", "S3nh4-Long4!",
        "--chave", "ACME-2026",
        "--cor", "#aa00aa",
    )
    assert "configurada" in saida

    config = ConfiguracaoInstancia.atual()
    assert config.nome_exibicao == "Nutri Acme"
    assert config.cor_primaria == "#aa00aa"
    assert config.ano_corte_ingredientes is None  # empresas novas sem corte (D-010)

    usuario = User.objects.get(username="ana")
    assert usuario.check_password("S3nh4-Long4!")
    assert usuario.groups.filter(name=settings.GRUPO_ADMINISTRADORES).exists()
    assert Membro.objects.filter(usuario=usuario).exists()
    assert Chave.objects.last().key == "ACME-2026"


def test_bootstrap_recusa_instancia_ja_configurada(db):
    ConfiguracaoInstancia.objects.create(nome_exibicao="Existente")
    with pytest.raises(CommandError, match="já está configurada"):
        executar(
            "bootstrap_instancia", "--nome", "Outra", "--admin", "x",
            "--senha", "S3nh4-Long4!", "--chave", "K",
        )


def test_bootstrap_recusa_usuario_existente(db, membro):
    with pytest.raises(CommandError, match="já existe"):
        executar(
            "bootstrap_instancia", "--nome", "Nova", "--admin", "admin",
            "--senha", "S3nh4-Long4!", "--chave", "K",
        )


def test_empresa_nova_funciona_ponta_a_ponta(client, db):
    """Cenário de venda: provisionar, cadastrar membro com a chave e entrar."""
    executar(
        "bootstrap_instancia",
        "--nome", "Nutri Beta", "--admin", "gestor",
        "--senha", "S3nh4-Long4!", "--chave", "BETA-1",
    )
    resp = client.post(
        "/registrarMembro",
        {
            "nome": "nutricionista", "semestre": "2026.1", "email": "n@beta.com",
            "senha1": "Outr4-S3nh4!", "senha2": "Outr4-S3nh4!", "chave": "BETA-1",
        },
    )
    assert resp.status_code == 302
    assert client.post(
        "/loginUser", {"username": "nutricionista", "password": "Outr4-S3nh4!"}
    ).url == "/listaFichas"
    # branding da instância aparece na interface
    assert "Nutri Beta" in client.get("/listaFichas").content.decode()
