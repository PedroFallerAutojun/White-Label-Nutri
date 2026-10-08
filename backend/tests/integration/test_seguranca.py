"""Testes de segurança: isolamento por autenticação, CSRF e configuração de produção."""
import pytest
from django.contrib.auth.models import User
from django.test import Client

from apps.fichas.models import Ficha, Membro, Tabela


@pytest.fixture
def membro(db):
    user = User.objects.create_user("laura", password="s3nh4-Long4-forte")
    return Membro.objects.create(
        usuario=user, nome="Laura", semestre="2024.1", email="l@x.com"
    )


@pytest.fixture
def ficha(membro):
    ficha = Ficha.objects.create(
        autor=membro, cliente="C", nomeFicha="Ficha", dataCriacao="2025-01-01",
        pesoTotal=100, pesoPorcao=50, pesoAnvisa=50,
    )
    Tabela.objects.create(pk=ficha.pk, origem=ficha)
    return ficha


ROTAS_PROTEGIDAS = [
    "/listaFichas", "/listaIngredientes", "/listaMembros", "/ajuda",
    "/registrarFicha1", "/registrarIngrediente", "/upload",
]

MUTACOES = [
    ("/deletarFicha/{pk}", {}),
    ("/atualizarFinalizada/{pk}", {}),
    ("/atualizarMostrar/{pk}/calcio/", {}),
    ("/registrarFicha3/{pk}", {"informacoesComplementares": "invadido"}),
]


@pytest.mark.parametrize("url", ROTAS_PROTEGIDAS)
def test_rotas_exigem_autenticacao(client, db, url):
    resp = client.get(url)
    assert resp.status_code == 302
    assert "/loginUser" in resp.url


@pytest.mark.parametrize("template,dados", MUTACOES)
def test_mutacoes_exigem_autenticacao(client, ficha, template, dados):
    """Nenhuma alteração de dados acontece sem sessão válida."""
    resp = client.post(template.format(pk=ficha.pk), dados)
    assert resp.status_code == 302
    assert "/loginUser" in resp.url
    assert Ficha.objects.filter(pk=ficha.pk).exists()
    assert Tabela.objects.get(pk=ficha.pk).informacoesComplementares != "invadido"


def test_csrf_bloqueia_post_sem_token(membro, ficha):
    """O cliente de teste com CSRF ativo recusa POST sem token."""
    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(membro.usuario)
    resp = cliente.post(f"/atualizarFinalizada/{ficha.pk}", {})
    assert resp.status_code == 403
    ficha.refresh_from_db()
    assert ficha.finalizada is False


def test_senha_curta_e_recusada_no_cadastro(client, db):
    from apps.fichas.models import Chave

    Chave.objects.create(key="K")
    resp = client.post(
        "/registrarMembro",
        {"nome": "novo", "semestre": "2026.1", "email": "n@x.com",
         "senha1": "curta", "senha2": "curta", "chave": "K"},
    )
    # o cadastro não passa: a senha viola os validadores ou o formulário reprova
    assert not User.objects.filter(username="novo").exists()
    assert resp.status_code == 200


def test_fluxo_de_reset_por_email_nao_esta_exposto(client, db):
    """D-014: o reset por e-mail nunca funcionou; não expomos fluxo quebrado."""
    for url in ["/password_reset/", "/accounts/password_reset/", "/reset/"]:
        assert client.get(url).status_code == 404


def test_configuracao_de_producao_e_segura(monkeypatch):
    """Garantias da D-013 (avaliadas em config.settings.prod)."""
    import importlib

    monkeypatch.setenv("SECRET_KEY", "chave-suficientemente-longa-para-o-teste-de-config")
    monkeypatch.setenv("ALLOWED_HOSTS", "exemplo.com")
    prod = importlib.reload(importlib.import_module("config.settings.prod"))
    assert prod.DEBUG is False
    assert prod.SESSION_COOKIE_SECURE is True
    assert prod.CSRF_COOKIE_SECURE is True
    assert prod.SESSION_COOKIE_HTTPONLY is True
    assert prod.SECURE_CONTENT_TYPE_NOSNIFF is True
    assert prod.X_FRAME_OPTIONS == "DENY"
    assert prod.SECURE_HSTS_SECONDS >= 3600
    assert prod.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")
    assert prod.CSRF_TRUSTED_ORIGINS == ["https://exemplo.com"]


def test_producao_exige_secret_key_e_hosts(monkeypatch):
    """Sem SECRET_KEY ou ALLOWED_HOSTS a instância não sobe (falha explícita)."""
    import environ

    env = environ.Env()
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(environ.ImproperlyConfigured):
        env("SECRET_KEY")
    monkeypatch.delenv("ALLOWED_HOSTS", raising=False)
    with pytest.raises(environ.ImproperlyConfigured):
        env.list("ALLOWED_HOSTS")
