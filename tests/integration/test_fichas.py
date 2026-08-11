"""Testes de integração do wizard de fichas, receita, tabela e rótulo (E3/E4)."""
import pytest
from django.contrib.auth.models import User

from apps.fichas.models import Ficha, Ficha_Ingrediente, Ingrediente, Membro, Nutriente, Tabela
from apps.plataforma.models import ConfiguracaoInstancia


@pytest.fixture
def membro(db):
    user = User.objects.create_user("laura", password="s3nh4-forte")
    return Membro.objects.create(
        usuario=user, nome="Laura", semestre="2024.1", email="l@x.com"
    )


@pytest.fixture
def logado(client, membro):
    client.force_login(membro.usuario)
    return client


@pytest.fixture
def ingrediente(membro):
    """Farinha: 10 g de proteína, 70 g de carboidrato e 2 g de gordura por 100 g."""
    ing = Ingrediente.objects.create(
        autorIng=membro,
        nomeIng="Farinha de trigo",
        origemDosDados="TACO",
        dataCriacao="2024-01-10",
        qtdeDoIngrediente=100,
        proteinas=10,
        proteinas_100g=10,
        carboidratos=70,
        carboidratos_100g=70,
        gordTotais=2,
        gordTotais_100g=2,
        sodio=500,
        sodio_100g=500,
    )
    return ing


@pytest.fixture
def ficha(membro):
    ficha = Ficha.objects.create(
        autor=membro,
        cliente="Padaria",
        nomeFicha="Pão de teste",
        dataCriacao="2025-05-01",
        pesoTotal=200,
        pesoPorcao=100,
        pesoAnvisa=50,
        medCaseiraPorcao="1 fatia",
    )
    Tabela.objects.create(pk=ficha.pk, origem=ficha)
    return ficha


# ------------------------------------------------------------------ wizard 1/3


def test_criar_ficha_cria_tabela_com_mesmo_pk(logado, membro):
    resp = logado.post(
        "/registrarFicha1",
        {
            "autor": membro.pk,
            "nomeFicha": "Bolo",
            "cliente": "Cliente X",
            "pesoTotal": 500,
            "pesoPorcao": 100,
            "pesoAnvisa": 50,
            "dataCriacao": "01/05/2025",
            "medCaseiraPorcao": "1 pedaço",
        },
    )
    nova = Ficha.objects.get(nomeFicha="Bolo")
    assert resp.status_code == 302
    assert resp.url == f"/registrarFicha2/{nova.pk}"
    assert Tabela.objects.filter(pk=nova.pk, origem=nova).exists()  # BR-015


# ------------------------------------------------------------------ wizard 2/3


def test_adicionar_ingrediente_recalcula_tabela(logado, ficha, ingrediente):
    resp = logado.post(
        f"/registrarFicha2/{ficha.pk}",
        {
            "ingExtra": "Farinha de trigo",
            "nomeFantasia": "Farinha",
            "pesoBruto": 100,
            "pesoLiquido": 100,
            "medidaCaseira": "1 xíc",
        },
    )
    assert resp.status_code == 302
    tabela = Tabela.objects.get(pk=ficha.pk)
    # 100 g de farinha: 10 g proteína; peso total 200 g → 5 g/100 g; porção 50 g → 2,5 g
    assert tabela.proteinas == pytest.approx(10)
    assert tabela.proteinas_Porcao == pytest.approx(2.5)
    assert tabela.proteinas_Arred == pytest.approx(2.5)
    # Energia por Atwater (BR-003): 10*4 + 70*4 + 2*9 = 338 kcal
    assert tabela.energiakcal == pytest.approx(338)
    ficha.refresh_from_db()
    assert ficha.pesoLiquidoPreparacao == pytest.approx(100)
    assert ficha.numPorcoes == 2  # 100 / 50


def test_ingrediente_inexistente_mostra_erro(logado, ficha):
    resp = logado.post(
        f"/registrarFicha2/{ficha.pk}",
        {"ingExtra": "Não existe", "nomeFantasia": "X", "pesoBruto": 1, "pesoLiquido": 1,
         "medidaCaseira": ""},
        follow=True,
    )
    assert "não foi encontrado" in resp.content.decode()
    assert not Ficha_Ingrediente.objects.exists()


def test_sem_pesos_nao_adiciona_ingrediente(logado, membro, ingrediente):
    ficha = Ficha.objects.create(
        autor=membro, cliente="C", nomeFicha="Sem pesos", dataCriacao="2025-01-01",
        pesoTotal=0, pesoPorcao=0,
    )
    Tabela.objects.create(pk=ficha.pk, origem=ficha)
    resp = logado.post(
        f"/registrarFicha2/{ficha.pk}",
        {"ingExtra": "Farinha de trigo", "nomeFantasia": "F", "pesoBruto": 10,
         "pesoLiquido": 10, "medidaCaseira": ""},
        follow=True,
    )
    assert "peso total" in resp.content.decode()
    assert not Ficha_Ingrediente.objects.exists()  # BR-016


def test_nao_remove_ultimo_item_da_receita(logado, ficha, ingrediente):
    item = Ficha_Ingrediente.objects.create(
        ficha=ficha, ingrediente=ingrediente, pesoBruto=10, pesoLiquido=10,
        nomeFantasia="Farinha",
    )
    logado.post(f"/deletarItemReceita/{ficha.pk}/{item.pk}/")
    assert Ficha_Ingrediente.objects.filter(pk=item.pk).exists()  # BR-018


def test_remove_item_quando_ha_mais_de_um(logado, ficha, ingrediente):
    primeiro = Ficha_Ingrediente.objects.create(
        ficha=ficha, ingrediente=ingrediente, pesoBruto=10, pesoLiquido=10, nomeFantasia="A"
    )
    Ficha_Ingrediente.objects.create(
        ficha=ficha, ingrediente=ingrediente, pesoBruto=20, pesoLiquido=20, nomeFantasia="B"
    )
    logado.post(f"/deletarItemReceita/{ficha.pk}/{primeiro.pk}/")
    assert not Ficha_Ingrediente.objects.filter(pk=primeiro.pk).exists()


def test_editar_item_recalcula_tabela(logado, ficha, ingrediente):
    """B12 corrigido: salvar o item recalcula (o original não recalculava)."""
    item = Ficha_Ingrediente.objects.create(
        ficha=ficha, ingrediente=ingrediente, pesoBruto=100, pesoLiquido=100,
        nomeFantasia="Farinha",
    )
    logado.post(f"/registrarFicha2/{ficha.pk}", {})  # garante estado inicial
    logado.post(
        f"/editarItemReceita/{ficha.pk}/{item.pk}/",
        {"nomeFantasia": "Farinha", "pesoBruto": 50, "pesoLiquido": 50, "medidaCaseira": ""},
    )
    tabela = Tabela.objects.get(pk=ficha.pk)
    assert tabela.proteinas == pytest.approx(5)  # 50 g × 10/100


# ------------------------------------------------------------------ wizard 3/3


def test_toggle_mostrar_inverte_visibilidade(logado, ficha):
    tabela = Tabela.objects.get(pk=ficha.pk)
    inicial = tabela.calcio_Mostrar
    logado.post(f"/atualizarMostrar/{ficha.pk}/calcio/")
    tabela.refresh_from_db()
    assert tabela.calcio_Mostrar is not inicial


def test_toggle_nutriente_desconhecido_nao_quebra(logado, ficha):
    resp = logado.post(f"/atualizarMostrar/{ficha.pk}/inexistente/", follow=True)
    assert resp.status_code == 200
    assert "desconhecido" in resp.content.decode()


def test_nutriente_extra_e_criado_e_removido(logado, ficha):
    logado.post(
        f"/registrarFicha3/{ficha.pk}",
        {"acao": "nutriente", "nomeNutri": "Cafeína", "qtde": 30, "qtde_Arred": 30,
         "medida": "mg", "qtde_VD": 0},
    )
    extra = Nutriente.objects.get(nomeNutri="Cafeína")
    logado.post(f"/deletarNutrienteExtra/{extra.pk}")
    assert not Nutriente.objects.filter(pk=extra.pk).exists()


def test_informacoes_complementares_salvam_e_vao_para_rotulo(logado, ficha):
    resp = logado.post(
        f"/registrarFicha3/{ficha.pk}",
        {"informacoesComplementares": "CONTÉM GLÚTEN."},
    )
    assert resp.url == f"/fichaX/{ficha.pk}"
    assert Tabela.objects.get(pk=ficha.pk).informacoesComplementares == "CONTÉM GLÚTEN."


# -------------------------------------------------------------------- rótulo


def test_rotulo_mostra_tabela_e_ingredientes(logado, ficha, ingrediente):
    Ficha_Ingrediente.objects.create(
        ficha=ficha, ingrediente=ingrediente, pesoBruto=100, pesoLiquido=100,
        nomeFantasia="Farinha de trigo",
    )
    logado.post(
        f"/editarItemReceita/{ficha.pk}/{Ficha_Ingrediente.objects.first().pk}/",
        {"nomeFantasia": "Farinha de trigo", "pesoBruto": 100, "pesoLiquido": 100,
         "medidaCaseira": ""},
    )
    corpo = logado.get(f"/fichaX/{ficha.pk}").content.decode()
    assert "INFORMAÇÃO NUTRICIONAL" in corpo
    assert "Farinha de trigo" in corpo
    assert "2 porções" in corpo  # BR-011: 100 / 50 exato


def test_rotulo_de_ficha_sem_tabela_nao_quebra(logado, membro):
    """B4 corrigido: ficha órfã (como as 16 do backup) não gera mais erro 500."""
    orfa = Ficha.objects.create(
        autor=membro, cliente="C", nomeFicha="Órfã", dataCriacao="2021-01-01",
        pesoTotal=100, pesoPorcao=50, pesoAnvisa=50,
    )
    assert not Tabela.objects.filter(pk=orfa.pk).exists()
    resp = logado.get(f"/fichaX/{orfa.pk}")
    assert resp.status_code == 200
    assert Tabela.objects.filter(pk=orfa.pk).exists()


def test_rotulo_sem_pesos_nao_quebra(logado, membro):
    """B15 corrigido: pesos de porção nulos (ficha 1273 do backup) não geram 500."""
    ficha = Ficha.objects.create(
        autor=membro, cliente="C", nomeFicha="Sem pesos", dataCriacao="2021-01-01",
        pesoPorcao=None, pesoAnvisa=None,
    )
    Tabela.objects.create(pk=ficha.pk, origem=ficha)
    resp = logado.get(f"/fichaX/{ficha.pk}")
    assert resp.status_code == 200
    assert "0 porções" in resp.content.decode()


def test_rotulo_exibe_biotina_sem_quebrar(logado, ficha):
    """B2 corrigido: o original crashava ao exibir biotina."""
    tabela = Tabela.objects.get(pk=ficha.pk)
    tabela.biotina_Mostrar = True
    tabela.biotina_Arred = 3.5
    tabela.save()
    corpo = logado.get(f"/fichaX/{ficha.pk}").content.decode()
    assert "Biotina" in corpo


def test_lupa_aparece_quando_alto_em_sodio(logado, ficha):
    """BR-012: sódio ≥ 600 mg/100 g exige o selo frontal."""
    tabela = Tabela.objects.get(pk=ficha.pk)
    tabela.sodio_100g = 700
    tabela.save()
    corpo = logado.get(f"/fichaX/{ficha.pk}").content.decode()
    assert "data:image/png;base64," in corpo
    assert "Rotulagem frontal" in corpo


def test_finalizada_e_um_toggle(logado, ficha):
    logado.post(f"/atualizarFinalizada/{ficha.pk}")
    ficha.refresh_from_db()
    assert ficha.finalizada is True
    logado.post(f"/atualizarFinalizada/{ficha.pk}")
    ficha.refresh_from_db()
    assert ficha.finalizada is False


def test_excluir_ficha_apaga_em_cascata(logado, ficha, ingrediente):
    Ficha_Ingrediente.objects.create(
        ficha=ficha, ingrediente=ingrediente, pesoBruto=1, pesoLiquido=1, nomeFantasia="F"
    )
    logado.post(f"/deletarFicha/{ficha.pk}")
    assert not Ficha.objects.filter(pk=ficha.pk).exists()
    assert not Tabela.objects.filter(pk=ficha.pk).exists()
    assert not Ficha_Ingrediente.objects.exists()  # BR-020


# --------------------------------------------------------------- ingredientes


def test_ingrediente_normaliza_para_100g(logado, membro):
    """BR-001: valores informados para 50 g são normalizados para 100 g."""
    dados = {
        "autorIng": membro.pk,
        "nomeIng": "Açúcar",
        "composicao": "",
        "origemDosDados": "Marca X",
        "qtdeDoIngrediente": 50,
        "numRef": 0,
        "dataCriacao": "10/01/2025",
        "proteinas": 5,
    }
    for chave in ("gordTotais", "acucaresTotais", "carboidratos", "fibras", "energiakcal",
                  "energiaKJ"):
        dados[chave] = 0
    logado.post("/registrarIngrediente", dados)
    ing = Ingrediente.objects.get(nomeIng="Açúcar")
    assert ing.proteinas_100g == pytest.approx(10)  # 5 * 100 / 50


def test_nome_de_ingrediente_duplicado_e_recusado(logado, membro, ingrediente):
    resp = logado.post(
        "/registrarIngrediente",
        {"autorIng": membro.pk, "nomeIng": "Farinha de trigo", "composicao": "",
         "origemDosDados": "X", "qtdeDoIngrediente": 100, "numRef": 0,
         "dataCriacao": "10/01/2025"},
        follow=True,
    )
    assert "Já existe um ingrediente com esse nome" in resp.content.decode()
    assert Ingrediente.objects.filter(nomeIng="Farinha de trigo").count() == 1


def test_corte_por_ano_e_configuracao_da_instancia(logado, membro):
    """BR-017/D-010: sem configuração não há corte; com corte 2024, esconde antigos."""
    Ingrediente.objects.create(
        autorIng=membro, nomeIng="Antigo 2019", origemDosDados="TACO",
        dataCriacao="2019-09-26", qtdeDoIngrediente=100,
    )
    corpo = logado.post("/listaIngredientes", {}).content.decode()
    assert "Antigo 2019" in corpo

    ConfiguracaoInstancia.objects.create(nome_exibicao="Nutri Jr", ano_corte_ingredientes=2024)
    corpo = logado.post("/listaIngredientes", {}).content.decode()
    assert "Antigo 2019" not in corpo


def test_excluir_ingrediente_avisa_sobre_receitas(logado, ficha, ingrediente):
    Ficha_Ingrediente.objects.create(
        ficha=ficha, ingrediente=ingrediente, pesoBruto=1, pesoLiquido=1, nomeFantasia="F"
    )
    resp = logado.post(f"/deletarIngrediente/{ingrediente.pk}", follow=True)
    assert "removido de 1 receita" in resp.content.decode()


# ------------------------------------------------------------------ segurança


@pytest.mark.parametrize(
    "url",
    [
        "/listaFichas", "/listaIngredientes", "/registrarFicha1",
        "/registrarIngrediente", "/upload", "/ajuda",
    ],
)
def test_paginas_exigem_login(client, db, url):
    resp = client.get(url)
    assert resp.status_code == 302
    assert "/loginUser" in resp.url


@pytest.mark.parametrize(
    "template",
    [
        "/atualizarFinalizada/{pk}",
        "/deletarFicha/{pk}",
        "/atualizarMostrar/{pk}/calcio/",
    ],
)
def test_mutacoes_recusam_get(logado, ficha, template):
    """B10 corrigido: mutações só por POST."""
    resp = logado.get(template.format(pk=ficha.pk))
    assert resp.status_code == 405


def test_ficha_inexistente_devolve_404(logado):
    assert logado.get("/fichaX/999999").status_code == 404
