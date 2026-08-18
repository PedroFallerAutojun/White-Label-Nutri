# Prints — criação de uma nova receita

Capturas do fluxo completo de cadastro de uma ficha técnica, feitas numa instância
local vazia (`bootstrap_instancia`) com seis ingredientes da TACO cadastrados e a
receita de exemplo **Bolo de chocolate caseiro** (cliente "Confeitaria Doce Ponto").

O wizard tem três etapas (`registrarFicha1` → `registrarFicha2` → `registrarFicha3`)
e termina no rótulo final (`fichaX`).

| # | Print | Tela |
|---|-------|------|
| 01 | [01-login.png](01-login.png) | Login (`/loginUser`) |
| 02 | [02-fichas-registradas.png](02-fichas-registradas.png) | Fichas registradas — ponto de partida, botão **Nova ficha** |
| 03 | [03-etapa1-dados-base.png](03-etapa1-dados-base.png) | **Etapa 1/3** — dados base preenchidos: autor, cliente, nome, peso total (1096 g), porção cliente (80 g), porção Anvisa (60 g), medida caseira e data |
| 04 | [04-etapa2-receita-vazia.png](04-etapa2-receita-vazia.png) | **Etapa 2/3** — receita recém-criada, ainda sem ingredientes |
| 05 | [05-etapa2-adicionando-ingrediente.png](05-etapa2-adicionando-ingrediente.png) | Etapa 2 — formulário de ingrediente preenchido (busca por *datalist*, nome fantasia, pesos bruto/líquido, medida caseira) |
| 06 | [06-etapa2-receita-montada.png](06-etapa2-receita-montada.png) | Etapa 2 — seis ingredientes na receita; os cartões do topo já mostram o cálculo (1096 g de preparação, 191 kcal por porção) |
| 07 | [07-etapa3-tabela-nutricional.png](07-etapa3-tabela-nutricional.png) | **Etapa 3/3** — nutrientes calculados com total, por 100 g, por porção, arredondado e %VD, e a coluna **No rótulo** (BR-030) |
| 08 | [08-etapa3-informacoes-complementares.png](08-etapa3-informacoes-complementares.png) | Etapa 3 — informações complementares (alérgicos) preenchidas antes de **Salvar e ver rótulo** |
| 09 | [09-rotulo-final.png](09-rotulo-final.png) | Rótulo final — modelos vertical e linear, lista de ingredientes e alérgicos |
| 10 | [10-ficha-na-listagem.png](10-ficha-na-listagem.png) | A ficha nova na listagem, com status **Em edição** |

## Como reproduzir

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
DATABASE_URL=postgres://postgres:postgres@127.0.0.1:5432/nutri .venv/bin/python manage.py migrate
DATABASE_URL=postgres://postgres:postgres@127.0.0.1:5432/nutri .venv/bin/python manage.py \
    bootstrap_instancia --nome "Nutri Demo" --admin admin --email admin@demo.local \
    --chave DEMO-2026 --senha "admin-local-123456"
DATABASE_URL=postgres://postgres:postgres@127.0.0.1:5432/nutri .venv/bin/python manage.py runserver
```

Os ingredientes de exemplo podem ser cadastrados pela tela **Ingredientes → Novo**
ou importados em lote pelo `/upload` (TXT da TACO separado por TAB, BR-023).
