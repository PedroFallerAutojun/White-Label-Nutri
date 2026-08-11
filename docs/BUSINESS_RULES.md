# Regras de Negócio — Nutri Jr

Formato: cada regra tem descrição, condição, resultado, onde foi encontrada e impacto.
Salvo indicação, todas são **[CONFIRMADO]** por leitura do código.

---

## Cálculo nutricional (núcleo do sistema)

### BR-001 — Ingrediente: normalização para 100 g
- **Descrição:** todo nutriente do ingrediente é informado para `qtdeDoIngrediente` gramas
  (default 100) e normalizado: `X_100g = X * 100 / qtdeDoIngrediente`. Valor `None` vira 0.
- **Onde:** `views.att100gIngrediente` (views.py:1233). Chamada ao registrar/editar/upload.
- **Impacto:** base de todo o cálculo de receita.

### BR-002 — Soma da receita
- **Descrição:** para cada nutriente, `Tabela.X = Σ (ingrediente.X_100g / 100) * item.pesoLiquido`
  sobre os itens da receita. Usa **peso líquido** (não o bruto).
- **Onde:** `attTabela → adicionaValoresComBaseNaReceita` (views.py:163).

### BR-003 — Energia por Atwater (recalculada, não somada)
- **Descrição:** a energia da tabela NÃO é a soma das energias dos ingredientes:
  `kcal = proteinas*4 + carboidratos*4 + gordTotais*9`; `kJ = kcal * 4.184`.
- **Onde:** `attTabela → calculaEnergiaAtwater` (views.py:213).
- **Impacto:** divergências esperadas vs. energia declarada nas fontes (TACO).

### BR-004 — Valores por 100 g da preparação
- **Descrição:** `X_100g = X * 100 / ficha.pesoTotal` (peso total INFORMADO pelo usuário,
  não a soma dos pesos líquidos). Se pesoTotal ausente/0 → tudo 0.
- **Onde:** `attTabela → atualizaNutriente_100g` (views.py:226).
- **Impacto:** pesoTotal considera perdas/rendimento de cocção; regra essencial.

### BR-005 — Valores por porção
- **Descrição:** `X_Porcao = X_100g / 100 * (pesoAnvisa ou pesoPorcao)`. O peso da porção
  ANVISA tem precedência; o `pesoPorcao` ("porção cliente") é fallback.
- **Onde:** `attTabela → atualizaNutriente_Porcao` (views.py:326).

### BR-006 — Arredondamento ANVISA
- **Descrição:** aplicado a `X_Arred` (porção) **e reaplicado sobre `X_100g`** (o valor por
  100 g persistido passa a ser o arredondado!):
  - kcal/kJ → inteiro;
  - valor ≥ 10 → inteiro; 1 ≤ valor < 10 → 1 casa; valor < 1 → 1 casa (g) ou 2 casas (mg/µg);
  - arredondamento "half-down" (32,5 → 32) via `round_half_down`.
- **Onde:** `arredondaNutriente_ANVISA` (views.py:29), `atualizaNutriente_Arred` (views.py:378).
- **Impacto:** ⚠️ efeito colateral: `X_100g` perde precisão a cada `attTabela`. A nova versão
  deve reproduzir o RESULTADO exibido, mas é candidata a guardar o valor bruto separado.

### BR-007 — Quantidades declaráveis como zero (condição para zerar)
- **Descrição:** antes de arredondar, zera se (por porção e por 100 g, avaliados separadamente):
  proteínas ≤ 0,5 g; carboidratos ≤ 0,5 g; fibras ≤ 0,5 g; kcal ≤ 4; kJ ≤ 17; sódio ≤ 5 mg;
  gordSat ≤ 0,2 g; gordTrans ≤ 0,2 g; gordTotais ≤ 0,5 g **e** gordSat ≤ 0,5 **e** gordTrans ≤ 0,5
  **e** gordMono == 0 **e** gordPoli == 0 (na condição da porção o código usa `gordPoli` total —
  provável typo, preservar comportamento até decisão; na de 100 g usa `gordPoli_100g`).
- **Onde:** views.py:388-435.

### BR-008 — % Valor Diário
- **Descrição:** `X_VD = round(100 * X_Arred / referência)` (sobre o valor JÁ arredondado).
  Referências (dieta 2.000 kcal): proteínas 50 g, gordTotais 65 g, carboidratos 300 g, fibras 25 g,
  kcal 2000, kJ 8400, cálcio 1000 mg, ferro 14 mg, magnésio 420 mg, fósforo 700 mg, sódio 2000 mg,
  zinco 11 mg, cobre 0,9 mg, manganês 3 mg, vitC 100 mg, tiamina 1,2, riboflavina 1,2, niacina 15,
  gordSat 20 g, colesterol 300 mg, açúcares adicionados 50 g, ômega-6 18, ômega-3 4000, vitD 15,
  vitE 15, vitK 120, biotina 30, ác. fólico 400, ác. pantotênico 5, B12 2,4, cloreto 2300,
  cromo 35, flúor 4, iodo 150, molibdênio 45, **selênio 11** (⚠️ diverge da IN 75/2020, que é 34 µg
  — preservar ou corrigir? [PRECISA SER VALIDADO]), colina 550.
  Sem VD (forçados a 0): potássio, retinol, RE, RAE, piridoxina, gordTrans, gordPoli, gordMono.
- **Onde:** `atualizaValorDiario` (views.py:448).

### BR-009 — Açúcares totais sem %VD
- **Descrição:** na tabela final, açúcares totais exibe %VD em branco (sem "0", "-" ou "(**)"),
  conforme RDC 429/2020 art. 12 §1º. Gorduras trans usa `vd_trans = 0` fixo.
- **Onde:** `fichaX → montarTabelaFinal` (views.py:~835).

### BR-010 — Número de porções (persistido)
- **Descrição:** `ficha.numPorcoes = int(pesoPorcao / pesoAnvisa)` (trunca); 0 se algum ausente.
- **Onde:** `attTabela` (views.py:442). Nota: fichas antigas foram gravadas com fórmula anterior
  (pesoTotal/pesoAnvisa); por isso a exibição recalcula (BR-011).

### BR-011 — Número de porções (exibição ANVISA)
- **Descrição:** na fichaX: exato → "10 porções"; quebrado e > 3 → "Cerca de N porções";
  quebrado e ≤ 3 → arredonda ao 1/4 mais próximo em número misto ("1 e 1/2 porções",
  "3/4 porção"); singular/plural corretos; 0/ausente → "0 porções".
- **Onde:** `fichaX → calcularNumPorcoes` (views.py:~798).

### BR-012 — Lupas "ALTO EM" (rotulagem frontal, alimentos sólidos)
- **Descrição:** produto é ALTO EM se, por 100 g: açúcares adicionados ≥ 15 g;
  gorduras saturadas ≥ 6 g; sódio ≥ 600 mg. As 7 combinações escolhem uma imagem
  (PNG base64 embutido em views.py) exibida no rótulo; nenhuma → sem lupa.
- **Onde:** `Tabela.nutrientes_altos` (models.py:635), `fichaX` (views.py:755+).

### BR-013 — Formatação numérica no rótulo
- **Descrição:** valores inteiros exibidos sem ",0"; decimais com vírgula (`tira_zero`).
  Coluna "por 100 g" recebe a mesma limpeza. `pesoAnvisa` exibido como inteiro sem zero.
- **Onde:** `fichaX → tira_zero` (views.py:~785).

### BR-014 — Lista de ingredientes do rótulo
- **Descrição:** itens da receita ordenados por `pesoLiquido` DESC; cada um exibido pelo
  `nomeFantasia`, seguido de `(composicao)` se o ingrediente tiver composição; separados por
  vírgula, termina com "."; primeira letra maiúscula (capitalize — o resto vira minúsculo).
- **Onde:** `fichaX → ordenarIngredientesPorQuantidade` (views.py:~975).

---

## Fichas e receitas

### BR-015 — Tabela criada junto com a ficha, com MESMO pk
- **Descrição:** ao criar ficha, cria-se `Tabela(pk=ficha.pk, origem=ficha)` se não existir.
  Diversas views assumem `Tabela.objects.get(pk=pk_da_ficha)`.
- **Onde:** `registrarFichaBase` (views.py:87).
- **Impacto:** invariante crítico para compatibilidade com o banco antigo.

### BR-016 — Adição de item na receita
- **Descrição:** só adiciona se `pesoTotal != 0` e `pesoPorcao != 0` na ficha; ingrediente é
  buscado por NOME EXATO digitado (datalist com autocomplete); inexistente → mensagem de erro.
  Após adicionar, recalcula toda a tabela (attTabela).
- **Onde:** `editarFichaReceita` (views.py:526).

### BR-017 — Ingredientes disponíveis: só criados a partir de 2024
- **Descrição:** a lista de ingredientes (tela e datalist da receita) filtra
  `dataCriacao.year >= 2024` — esconde a carga TACO de 2019 e legados. O filtro de busca da
  tela, porém, pesquisa SEM esse corte (inconsistência preservável).
- **Onde:** `editarFichaReceita` (views.py:533), `listaIngredientes` (views.py:1214).
- **[PRECISA SER VALIDADO]** se é intencional/definitivo.

### BR-018 — Não remover o último item da receita
- **Descrição:** `deletarItemReceita` só deleta se a receita tem > 1 item.
- **Onde:** views.py:570.

### BR-019 — Edição de item da receita
- **Descrição:** editar abre tela própria; salvar grava nomeFantasia, pesos e medida caseira.
  ⚠️ `salvarReceita` NÃO chama attTabela; o recálculo acontece quando `editarItemReceita` é
  aberto novamente ou em qualquer outro evento que dispare attTabela. [CONFIRMADO — quirk]
- **Onde:** views.py:583-607.

### BR-020 — Exclusões definitivas em cascata
- **Descrição:** deletar ficha (POST + confirm no front) apaga Tabela, itens e nutrientes extras
  (CASCADE). Deletar ingrediente apaga os itens de receita que o usam (CASCADE — receitas
  existentes PERDEM o item silenciosamente). Sem soft delete.
- **Onde:** `deletarFicha`, `deletarIngrediente`; FKs CASCADE nos models.

### BR-021 — Finalizada é um toggle livre
- **Descrição:** `atualizarFinalizada` inverte o booleano; usado como selo visual "FINALIZADA"
  na fichaX e na listagem; não bloqueia edição.
- **Onde:** views.py:1027.

---

## Ingredientes

### BR-022 — Nome de ingrediente único (validação na view)
- **Descrição:** registrar/editar recusa `nomeIng` já existente (case-sensitive, sem constraint
  de banco — duplicatas antigas podem existir).
- **Onde:** `registrarIngrediente`, `editarIngrediente` (views.py:1285, 1302).

### BR-023 — Upload TACO
- **Descrição:** TXT separado por TAB (exportado do Excel), 1ª linha ignorada;
  `update_or_create` com autor = primeiro Membro, `dataCriacao = 2019-09-26` fixa,
  origem = coluna 0, numRef = coluna 1, nome = coluna 2; mapeamento fixo de colunas
  (kcal=4, kJ=5, proteínas=6, lipídeos=7, colesterol=8, carboidratos=9, fibras=10, ...);
  **gordTrans = col52 + col53 (18:1t + 18:2t)**. Depois recalcula _100g de TODOS os ingredientes.
- **Onde:** `upload` (views.py:1321).

---

## Membros, chave e administração

### BR-024 — Cadastro com chave global
- **Descrição:** auto-cadastro exige digitar a chave atual (`Chave.objects.last()`);
  valida senhas iguais e username inexistente; cria `User` + `Membro` ligados; faz logout de
  quem estiver logado antes de exibir o formulário.
- **Onde:** `registrarMembro` (views.py:1156).

### BR-025 — Privilégios do admin por username
- **Descrição:** usuário com username exato `admin` vê a chave e os painéis de: trocar chave
  (insere nova linha em Chave), trocar senha de qualquer membro, excluir membro.
- **Onde:** `listaMembros` (views.py:1047); templates.

### BR-026 — Exclusão de membro com transferência de autoria
- **Descrição:** ao excluir um membro escolhe-se um destino (≠ origem); fichas e ingredientes
  têm a autoria transferida ANTES de deletar o `User` (que cascateia o Membro). Mensagem
  informa quantos itens foram transferidos.
- **Onde:** `deletaMembro` (views.py:1109), `ApagarMembro.clean` (forms.py:152).

### BR-027 — Login sempre derruba sessão anterior
- **Descrição:** abrir a página de login (ou de cadastro) faz `logout()` imediato.
  Falha de autenticação → mensagem "Não foi possível fazer login" e redirect para listaFichas
  (que devolve ao login por exigir autenticação).
- **Onde:** `loginUser` (views.py:1187).

---

## Filtros e listagens

### BR-028 — Filtros por contains (case-sensitive)
- **Descrição:** listas de fichas e ingredientes filtram com `__contains` (E lógico dos campos);
  fichas ordenadas por `-dataCriacao`; ingredientes e selects de autor por nome (case-insensitive
  via Lower). Filtro é via POST (não persiste na URL).
- **Onde:** `listaFichas` (views.py:62), `listaIngredientes` (views.py:1214), forms.

### BR-029 — Truncamento visual na tela da tabela (passo 3)
- **Descrição:** valores brutos/100g/porção exibidos com no máximo 5 casas via template tag
  `truncar` (corta, não arredonda).
- **Onde:** `templatetags/trunca_numeros.py`, `tabelaNutricional.html`.

### BR-030 — Estrutura fixa da tabela final
- **Descrição:** a fichaX fatia a lista de linhas: [0:5] antes de trans, [5] = linha trans
  (borda tracejada), [6:-1], [-1] = última (fecha caixa). Linhas indentadas: açúcares
  totais/adicionados, gordSat/Trans/Mono/Poli, colesterol. Valor energético só aparece se
  kcal E kJ estiverem marcados como mostrar.
- **Onde:** `fichaX` (views.py:~960), `fichax.html`.
