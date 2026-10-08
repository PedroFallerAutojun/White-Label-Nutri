"""Testes de membros, chave de cadastro e administração da instância (E5)."""
import pytest
from django.conf import settings
from django.contrib.auth.models import Group, User

from apps.fichas.models import Chave, Ficha, Ingrediente, Membro


@pytest.fixture
def chave(db):
    return Chave.objects.create(key="CHAVE-2026")


@pytest.fixture
def membro(db):
    user = User.objects.create_user("laura", password="s3nh4-forte")
    return Membro.objects.create(
        usuario=user, nome="Laura", semestre="2024.1", email="l@x.com"
    )


@pytest.fixture
def admin(db):
    user = User.objects.create_user("chefe", password="s3nh4-forte")
    grupo, _ = Group.objects.get_or_create(name=settings.GRUPO_ADMINISTRADORES)
    user.groups.add(grupo)
    return Membro.objects.create(usuario=user, nome="Chefe", semestre="2023.1", email="c@x.com")


DADOS_CADASTRO = {
    "nome": "novo.membro",
    "semestre": "2026.1",
    "email": "novo@x.com",
    "senha1": "S3nh4-Long4!",
    "senha2": "S3nh4-Long4!",
    "chave": "CHAVE-2026",
}


# ----------------------------------------------------------------- cadastro


def test_cadastro_com_chave_correta_cria_usuario_e_membro(client, chave):
    resp = client.post("/registrarMembro", DADOS_CADASTRO)
    assert resp.status_code == 302
    assert resp.url == "/loginUser"
    usuario = User.objects.get(username="novo.membro")
    membro = Membro.objects.get(usuario=usuario)
    assert membro.email == "novo@x.com"
    assert usuario.check_password("S3nh4-Long4!")  # senha utilizável


def test_cadastro_com_chave_incorreta_e_recusado(client, chave):
    dados = DADOS_CADASTRO | {"chave": "errada"}
    resp = client.post("/registrarMembro", dados)
    assert "Chave incorreta" in resp.content.decode()
    assert not User.objects.filter(username="novo.membro").exists()


def test_cadastro_com_senhas_diferentes_e_recusado(client, chave):
    dados = DADOS_CADASTRO | {"senha2": "outra-coisa"}
    resp = client.post("/registrarMembro", dados)
    assert "senhas não conferem" in resp.content.decode()
    assert not User.objects.filter(username="novo.membro").exists()


def test_cadastro_com_nome_existente_e_recusado(client, chave, membro):
    dados = DADOS_CADASTRO | {"nome": "laura"}
    resp = client.post("/registrarMembro", dados)
    assert "Já existe um usuário com esse nome" in resp.content.decode()
    assert User.objects.filter(username="laura").count() == 1


def test_cadastro_sem_chave_definida_e_recusado(client, db):
    resp = client.post("/registrarMembro", DADOS_CADASTRO)
    assert "Chave incorreta" in resp.content.decode()
    assert not User.objects.filter(username="novo.membro").exists()


# ------------------------------------------------------------ lista e papéis


def test_membro_comum_nao_ve_chave_nem_paineis(client, membro, chave):
    client.force_login(membro.usuario)
    corpo = client.get("/listaMembros").content.decode()
    assert "Laura" in corpo
    assert "CHAVE-2026" not in corpo
    assert "Definir nova chave" not in corpo


def test_administrador_ve_chave_e_paineis(client, admin, chave):
    client.force_login(admin.usuario)
    corpo = client.get("/listaMembros").content.decode()
    assert "CHAVE-2026" in corpo
    assert "Definir nova chave" in corpo


def test_superusuario_tambem_e_administrador(client, db, chave):
    User.objects.create_superuser("root", password="S3nh4-Long4!")
    client.force_login(User.objects.get(username="root"))
    assert "CHAVE-2026" in client.get("/listaMembros").content.decode()


# ------------------------------------------------- administração da instância


def test_admin_troca_chave(client, admin, chave):
    """B1 corrigido: no original esta ação quebrava (request.is_ajax)."""
    client.force_login(admin.usuario)
    resp = client.post("/mudaChave", {"key": "NOVA-CHAVE"}, follow=True)
    assert "Chave alterada com sucesso" in resp.content.decode()
    assert Chave.objects.last().key == "NOVA-CHAVE"


def test_admin_troca_senha_de_membro(client, admin, membro):
    """B1 corrigido."""
    client.force_login(admin.usuario)
    resp = client.post(
        "/trocaSenha",
        {"usuario": membro.usuario.pk, "nova_senha": "Nov4-S3nh4-Long4!"},
        follow=True,
    )
    assert "alterada com sucesso" in resp.content.decode()
    membro.usuario.refresh_from_db()
    assert membro.usuario.check_password("Nov4-S3nh4-Long4!")


def test_senha_fraca_e_recusada(client, admin, membro):
    client.force_login(admin.usuario)
    resp = client.post(
        "/trocaSenha", {"usuario": membro.usuario.pk, "nova_senha": "123"}, follow=True
    )
    assert "não pôde ser alterada" in resp.content.decode()
    membro.usuario.refresh_from_db()
    assert membro.usuario.check_password("s3nh4-forte")  # inalterada


def test_exclusao_de_membro_transfere_autoria(client, admin, membro):
    """BR-026 — fichas e ingredientes passam ao destino antes da exclusão."""
    Ficha.objects.create(
        autor=membro, cliente="C", nomeFicha="Ficha da Laura", dataCriacao="2025-01-01"
    )
    Ingrediente.objects.create(
        autorIng=membro, nomeIng="Ingrediente da Laura", origemDosDados="X",
        dataCriacao="2025-01-01", qtdeDoIngrediente=100,
    )
    client.force_login(admin.usuario)
    resp = client.post(
        "/deletaMembro",
        {"membroExcluido": membro.pk, "membroDestino": admin.pk},
        follow=True,
    )
    corpo = resp.content.decode()
    assert "Transferidos 1 fichas e 1 ingredientes" in corpo
    assert not Membro.objects.filter(pk=membro.pk).exists()
    assert not User.objects.filter(username="laura").exists()
    assert Ficha.objects.get(nomeFicha="Ficha da Laura").autor == admin
    assert Ingrediente.objects.get(nomeIng="Ingrediente da Laura").autorIng == admin


def test_exclusao_exige_membros_distintos(client, admin, membro):
    client.force_login(admin.usuario)
    resp = client.post(
        "/deletaMembro", {"membroExcluido": membro.pk, "membroDestino": membro.pk}, follow=True
    )
    assert "precisam ser distintos" in resp.content.decode()
    assert Membro.objects.filter(pk=membro.pk).exists()


# ------------------------------------------------------------------ segurança


@pytest.mark.parametrize("url", ["/mudaChave", "/trocaSenha", "/deletaMembro"])
def test_acoes_administrativas_exigem_papel_admin(client, membro, url):
    """No original, qualquer pessoa podia chamar esses endpoints."""
    client.force_login(membro.usuario)
    resp = client.post(url, {})
    assert resp.status_code == 302
    assert "/loginUser" in resp.url


@pytest.mark.parametrize("url", ["/mudaChave", "/trocaSenha", "/deletaMembro"])
def test_acoes_administrativas_recusam_get(client, admin, url):
    client.force_login(admin.usuario)
    assert client.get(url).status_code == 405


def test_lista_membros_exige_login(client, db):
    resp = client.get("/listaMembros")
    assert resp.status_code == 302
    assert "/loginUser" in resp.url
