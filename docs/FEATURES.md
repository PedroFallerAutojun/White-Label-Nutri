# Inventário de Funcionalidades — Nutri Jr

Colunas: Tela/URL de acesso; Permissão (L = logado, P = público, A = admin por username);
BD (R = leitura, C = cria, U = atualiza, D = deleta); Regras (ver BUSINESS_RULES.md).

| ID | Funcionalidade | Tela / URL | Perm. | BD | Regras | Dependências |
|----|----------------|------------|-------|-----|--------|--------------|
| F-01 | Login | `/` e `/loginUser` (login.html) | P | R auth | BR-027 | auth Django |
| F-02 | Logout | `/logoutUser` | P | — | — | — |
| F-03 | Cadastro de membro com chave | `/registrarMembro` | P | C User+Membro | BR-024 | Chave |
| F-04 | Listar membros | `/listaMembros` (usuarios_registrados.html) | L | R | BR-025 | — |
| F-05 | Ver chave atual | idem (só admin vê) | A | R Chave | BR-025 | — |
| F-06 | Trocar chave (AJAX) | `/mudaChave` | A* | C Chave | BR-025; usa `is_ajax()` (quebrado no Django 4.2) | jQuery |
| F-07 | Trocar senha de membro (AJAX) | `/trocaSenha` | A* | U auth_user | idem | jQuery |
| F-08 | Excluir membro c/ transferência (AJAX) | `/deletaMembro` | A* | U Ficha/Ingrediente, D User+Membro | BR-026; idem | jQuery |
| F-09 | Listar fichas + filtros | `/listaFichas` (fichas_registradas.html) | L | R | BR-028 | — |
| F-10 | Criar ficha (passo 1) | `/registrarFicha1` (registrarFichaBase.html) | L | C Ficha+Tabela | BR-015 | Membro |
| F-11 | Editar dados base (passo 1) | `/registrarFicha1/<pk>` | L | U Ficha, U Tabela | BR-001..BR-010 (recalcula) | attTabela |
| F-12 | Montar receita (passo 2) | `/registrarFicha2/<pk>` (receita.html) | L | C Ficha_Ingrediente, U Tabela | BR-016, BR-017, BR-002.. | attTabela, datalist |
| F-13 | Remover item da receita | `/deletarItemReceita/<pk>/<id>/` | ⚠ sem login | D item, U Tabela | BR-018 | attTabela |
| F-14 | Editar item da receita | `/editarItemReceita/<pk>/<id>/` (editarReceita.html) | ⚠ | U Tabela (recalc na abertura) | BR-019 | — |
| F-15 | Salvar item editado | `/salvarReceita` (POST) | ⚠ | U Ficha_Ingrediente | BR-019 (não recalcula) | — |
| F-16 | Tabela nutricional (passo 3) | `/registrarFicha3/<pk>` (tabelaNutricional.html) | L | R | BR-029 | — |
| F-17 | Adicionar nutriente extra manual | idem (form) | L | C Nutriente | — | — |
| F-18 | Remover nutriente extra | `/deletarNutrienteExtra/<pk>` | ⚠ | D Nutriente | — | — |
| F-19 | Alternar exibição de nutriente (olhinho) | `/atualizarMostrar/<pk>/<item>/` | ⚠ | U Tabela.X_Mostrar | BR-030 | — |
| F-20 | Salvar informações complementares | `/registrarFicha3/<pk>` (POST) | L | U Tabela | — | redirect fichaX |
| F-21 | Visualizar ficha/rótulo final | `/fichaX/<pk>` (fichax.html) | L | R | BR-009..BR-014, BR-030 | lupas, tira_zero |
| F-22 | Copiar rótulo p/ Google Docs | idem (botão JS) | L | — | BR-013 | execCommand('copy') |
| F-23 | Alternar "finalizada" | `/atualizarFinalizada/<pk>` | ⚠ | U Ficha | BR-021 | — |
| F-24 | Excluir ficha | `/deletarFicha/<pk>` (POST + confirm) | L | D Ficha (cascade Tabela, itens, nutrientes) | BR-020 | — |
| F-25 | Listar ingredientes + filtros | `/listaIngredientes` (ingredientes_registrados.html) | L | R | BR-017, BR-028 | — |
| F-26 | Registrar ingrediente | `/registrarIngrediente` (registrarIngrediente.html) | L | C Ingrediente | BR-001, BR-022 | att100g |
| F-27 | Editar ingrediente | `/editarIngrediente/<pk>` | L | U Ingrediente | BR-001, BR-022 | att100g |
| F-28 | Excluir ingrediente | `/deletarIngrediente/<pk>` (POST) | L | D Ingrediente (cascade itens de receita!) | BR-020 | — |
| F-29 | Upload TACO (TXT) | `/upload` (upload.html) | L | C/U Ingrediente em lote | BR-023 | csv, io |
| F-30 | Página de ajuda | `/ajuda` (ajuda.html) | L | — | — | — |
| F-31 | Django admin | `/admin/` | superuser | tudo | — | contrib.admin |
| F-32 | URLs de auth padrão do Django | `/password_reset/` etc. (include auth.urls) | P | — | e-mail NÃO configurado → reset de senha não funciona [PROVÁVEL] | — |
| F-33 | Mensagens flash (sucesso/erro) | todas as telas (base_layout) | — | — | — | contrib.messages |

⚠ = mutação sem `@login_required` e/ou via GET no original — a nova versão deve exigir
autenticação e método adequado (decisão de segurança, não muda o comportamento funcional
para usuários legítimos).

`*` = a UI só é exibida ao admin, mas o endpoint não valida ser admin.
