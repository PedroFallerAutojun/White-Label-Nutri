# Conformidade com o Backlog — Sprint 1 / Etapa 1 (NutriJr)

Documento de origem: *Backlog — Sprint 1 (Etapa 1: Correção do Sistema NutriJr)*,
08/06/2026. Contexto: as correções foram desenvolvidas e testadas num sistema irmão
(**Ceanut**) e portadas para o NutriJr.

Esta é a verificação item a item do que o **White-Label-Nutri** entrega em relação a cada
critério de aceite. Legenda: ✅ atendido · ⚠️ atendido com ressalva · 📋 fora do escopo de
código (operação/GitHub/Heroku) · ❓ decisão pendente do usuário.

## O que o backlog esclarece (e que estava em aberto na engenharia reversa)

Dois pontos que a leitura do código sozinha não resolvia:

1. **Task 5.1** — os valores por porção devem usar a **porção ANVISA**, não a do cliente.
   Aceite: *"a porção ANVISA aparece no rótulo independentemente de a porção do cliente
   estar preenchida; valores por porção baseados na porção ANVISA"*.
   → Confirma a causa do **B18**: as 73 fichas incoerentes do acervo tiveram a tabela
   gravada **antes** dessa correção, com a porção do cliente. Elas só passam a cumprir o
   critério de aceite depois de recalculadas.

2. **Task 5.3** — a fórmula do número de porções é
   `pesoPorcaoCliente / pesoAnvisa`, definida como *"quantas porções ANVISA cabem na
   porção do cliente"*, substituindo `pesoTotal / pesoAnvisa`.
   → **Encerra a dúvida levantada em 12/08/2026**: na ficha *Minicupcakes de goiaba*
   (total 231 g, porção cliente 60 g, porção ANVISA 38 g), "1 e 1/2 porções" é o
   resultado **correto e especificado** (60 ÷ 38 = 1,58). O valor `3` gravado no banco
   vem da fórmula antiga (`231 ÷ 60`), substituída pela Task 5.3.
   Implicação: **"porção do cliente" tem o papel de embalagem/porção comercial** — o
   rótulo declara quantas porções de referência cabem nela.

## Task 1 — Migração do repositório e controle de acesso

| Item | Situação |
|---|---|
| 1.1 Auditar titularidade | 📋 operação (GitHub/Heroku) |
| 1.2 Transferir repositório | 📋 operação — o código novo já vive em `PedroFallerAutojun/White-Label-Nutri` |
| 1.3 Reapontar deploy | 📋 operação. O repositório novo traz `Procfile` e `.github/workflows/testes.yml` prontos |
| 1.4 Remover acessos | 📋 operação |

## Task 2 — Preparação e verificação

| Item | Situação | Onde |
|---|---|---|
| 2.1 Backup de produção | ✅ o `BackupNutriJR` foi restaurado e **a restauração foi testada** | `docs/MIGRATION.md` |
| 2.2 Ambiente espelho | ✅ scripts para Windows/Linux/Docker, com restauração + saneamento + servidor; login e rótulo verificados sobre dados reais | `scripts/preparar_local*.ps1/.sh` |
| 2.3 Diff de models/migrations | ✅ **conclusão explícita: nenhuma migration destrutiva é necessária.** O schema do backup é idêntico ao dos models; o app novo `plataforma` acrescenta uma tabela (aditiva) | `docs/DATABASE.md §2`, `docs/MIGRATION.md` |
| 2.4 Configuração de ambiente | ✅ settings por variável de ambiente; produção exige `SECRET_KEY`/`ALLOWED_HOSTS` (falha no boot sem elas) | `config/settings/prod.py`, `.env.example` |

## Task 3 — Correções de cálculo nutricional

| Item | Situação | Evidência |
|---|---|---|
| 3.1 Atwater (4-4-9) | ✅ `kcal = P×4 + C×4 + G×9`; `kJ = kcal × 4,184` | `dominio/calculo.py` (BR-003); testes unitários + paridade em 1.556 fichas |
| 3.2 Arredondamento ANVISA | ✅ faixas ≥10 → inteiro, 1–10 → 1 casa, <1 g → 1 casa, <1 mg/µg → 2 casas, kcal/kJ → inteiro | `dominio/arredondamento.py` (BR-006); 19 casos de borda testados |

## Task 4 — Escopo da função de arredondamento

| Item | Situação | Evidência |
|---|---|---|
| 4.1 Função em nível de módulo | ✅ vive num módulo próprio, importável de qualquer lugar — não há como recriar o erro de "função não encontrada" | `dominio/arredondamento.py` |
| Arredondar também a coluna "por 100 g" | ✅ preservado (é o B8, documentado) | `calculo.py`, comentário sobre B8 |
| Proteção contra divisão por zero | ✅ `pesoTotal` ausente/zero → valores 0; pesos de porção ausentes → 0 (corrige B15/B16, que ainda quebravam o original) | testes `test_rotulo_sem_pesos_nao_quebra` |

## Task 5 — Correções de porção *(a mais importante do backlog)*

| Item | Situação | Evidência |
|---|---|---|
| 5.1 Usar `pesoAnvisa` no cálculo e na exibição | ✅ `peso_porcao = pesoAnvisa or pesoPorcao` no cálculo e no cabeçalho | `calculo.py` (BR-005), `rotulo.peso_anvisa_sem_zero` |
| 5.1 (dados) fichas antigas ainda com a porção do cliente | ⚠️ **73 fichas do acervo não cumprem o aceite** até serem recalculadas. O sistema **detecta e avisa** na tela do rótulo, com recálculo explícito por ficha; `auditar_tabelas` lista todas | B18, D-017 |
| 5.2 `calcularNumPorcoes()` com regras ANVISA | ✅ exato, "Cerca de N", número misto "1 e 1/2", frações de ¼, singular/plural | `rotulo.calcular_num_porcoes` (BR-011); testes dos casos exato, >3 e ≤3 |
| 5.3 Fórmula `pesoPorcaoCliente / pesoAnvisa` | ✅ implementada exatamente assim | `rotulo.num_porcoes_exibicao`, `calculo.py` (BR-010) |

## Task 6 — Filtro de frações (medida caseira)

| Item | Situação |
|---|---|
| 6.1 Definir o estado final | ❓ **decisão pendente.** Hoje o White-Label-Nutri segue o estado final do NutriJr/Ceanut: **sem** filtro decimal→fração — a medida caseira é texto livre, exibido como digitado ("1/2 xícara" funciona se digitado assim). Nenhum `fracao_filters` existe em nenhum dos dois sistemas |
| 6.2 Melhorias (opcional) | ❓ depende de 6.1. Se você quiser o filtro, o escopo do backlog é: ampliar o mapa (1/8, 2/5, 3/5, 4/5) e aceitar decimais sem zero à esquerda (`.5`) |

## Task 7 — Validação em ambiente espelho

| Item | Situação | Evidência |
|---|---|---|
| 7.1 Bateria com receitas reais | ⚠️ **feita, com uma diferença de método:** a comparação foi contra o **NutriJr original** (não contra a Ceanut, à qual não tenho acesso), e não em amostra — em **todas as 1.557 fichas** do acervo. Resultado: rótulos idênticos, zero divergência | `tests/integration/test_paridade_rotulo_e2e.py`, `docs/PARITY_MATRIX.md` |
| 7.2 Validar o %VD | ✅ `%VD = round(valor arredondado ÷ referência × 100)` com as 38 referências testadas. **Confirma a expectativa do backlog**: o %VD se corrige junto com a porção — nas fichas defasadas ele está errado porque o valor por porção está, e volta ao certo no recálculo | BR-008; `test_dominio_nutrientes.py`, `test_paridade_calculo.py` |
| 7.3 `makemigrations --check` | ✅ sem migrations pendentes; roda no CI a cada push | `.github/workflows/testes.yml` |

## Task 8 — Deploy seguro

| Item | Situação |
|---|---|
| 8.1 Publicar e verificar | 📋 operação. O que o código já oferece: `Procfile` com `release: migrate`, CI verde como pré-requisito, a preparação de MIGRATION.md §3, e a suíte de paridade para rodar contra o backup antes de publicar |

## Resumo

- **Todas as correções de código do backlog (Tasks 3, 4, 5) estão implementadas** e cobertas
  por testes, com paridade verificada em 1.557 fichas.
- **Task 7 vai além do pedido** em cobertura (acervo inteiro em vez de amostra), mas **fica
  abaixo em um ponto**: a comparação de referência foi com o NutriJr original, não com a Ceanut.
- **Duas pendências suas:** a decisão da Task 6.1 (filtro de frações) e o que fazer com as
  73 fichas que precisam de recálculo para cumprir a Task 5.1.
- Tasks 1, 2 (parcial) e 8 são operação em GitHub/Heroku, fora do código.
