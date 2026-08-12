# Matriz de Testes de Paridade — Original × Novo

Critério: mesma entrada, mesmo estado inicial, mesmo resultado, mesmo efeito no banco e
mesmo comportamento de erro. Status em 2026-08-11.

Legenda: ✅ paridade verificada · 🔧 comportamento corrigido por decisão (D-005) ·
🖐 requer validação manual (ninguém automatiza julgamento visual).

## 1. Paridade verificada por oráculo (código original como fonte de verdade)

| ID | Funcionalidade | Como foi comparado | Amostra | Resultado |
|----|----------------|--------------------|---------|-----------|
| P-01 | Pipeline de cálculo da tabela (BR-001..BR-010) | `attTabela` original executado sobre o backup (rollback) → `golden_paridade.json.gz`; comparação de total, /100 g, /porção, arredondado e %VD dos 46 nutrientes + pesoLiquidoPreparacao e numPorcoes | 1.556 fichas | ✅ **1.556/1.556 idênticas** (tolerância 1e-9) |
| P-02 | Montagem do rótulo (BR-009..BR-014, BR-030) | `golden_fichax.json.gz` (contexto real da view `fichaX` original) × `dominio.rotulo` | 1.557 fichas | ✅ **1.557/1.557** |
| P-03 | Rótulo renderizado ponta a ponta | nova aplicação lendo o banco legado; texto da tabela vertical (rótulo, unidade, 100 g, porção, %VD) + cabeçalho de porções | 1.557 fichas | ✅ **1.557/1.557**, zero erro HTTP |
| P-04 | Lupas "ALTO EM" (BR-012) | combinação canônica × hash da imagem do original | 1.557 fichas (557 com lupa) | ✅ todas conferem |
| P-05 | Nº de porções ANVISA (BR-011) | string exibida ("Cerca de N", frações, singular/plural) | 1.557 fichas | ✅ todas conferem |
| P-06 | Lista de ingredientes do rótulo (BR-014) | texto ordenado por peso, com composição | 1.557 fichas | ✅ conferem (empates de peso por equivalência de grupos — B17) |
| P-07 | Registro de nutrientes (unidades, ordem, indentação) | metadados × todas as linhas emitidas pelo original | 1.557 fichas | ✅ conferem |
| P-08 | Arredondamento ANVISA (BR-006/BR-007) | tabela de casos de borda (0,5 / 4 / 17 / 5 / 0,2; faixas <1, 1–10, ≥10; kcal/kJ) | 19 casos | ✅ |
| P-09 | Abertura de todas as fichas do acervo | HTTP status da view do rótulo | 1.574 fichas | ✅ **1.574 × HTTP 200** (original: 17 × HTTP 500) |

## 2. Paridade verificada por teste de integração (regra a regra)

| ID | Regra / funcionalidade | Original | Novo | Resultado |
|----|------------------------|----------|------|-----------|
| P-10 | Criar ficha cria Tabela com mesmo pk (BR-015) | cria manualmente | idem, via serviço | ✅ |
| P-11 | Adicionar item recalcula a tabela (BR-002..BR-010) | attTabela, 6 saves | 1 transação | ✅ mesmos valores |
| P-12 | Peso total/porção obrigatórios para adicionar item (BR-016) | bloqueia silenciosamente | bloqueia **com mensagem** | 🔧 melhoria de feedback |
| P-13 | Ingrediente inexistente na receita (BR-016) | mensagem de erro | mesma mensagem | ✅ |
| P-14 | Não remover o último item da receita (BR-018) | ignora o clique | ignora **e explica** | 🔧 melhoria de feedback |
| P-15 | Editar item da receita (BR-019) | **não** recalculava | recalcula | 🔧 B12 corrigido |
| P-16 | Alternar exibição de nutriente (BR-030) | 46 ramos `if/elif` | registro de nutrientes | ✅ |
| P-17 | Nutriente extra manual | cria/exclui | idem | ✅ |
| P-18 | Informações complementares | salva e vai ao rótulo | idem | ✅ |
| P-19 | Selo "finalizada" é toggle livre (BR-021) | inverte | inverte | ✅ |
| P-20 | Exclusão de ficha em cascata (BR-020) | apaga tabela, itens, extras | idem | ✅ |
| P-21 | Normalização do ingrediente para 100 g (BR-001) | att100gIngrediente | serviço equivalente | ✅ |
| P-22 | Nome de ingrediente duplicado (BR-022) | recusa com mensagem | mesma mensagem | ✅ |
| P-23 | Exclusão de ingrediente em uso (BR-020) | remove das receitas em silêncio | remove **e avisa quantas receitas** | 🔧 melhoria de feedback |
| P-24 | Corte de ingredientes ≥ 2024 (BR-017) | fixo no código | configuração da instância (2024 na Nutri Jr) | ✅ D-010 |
| P-25 | Filtros das listas (BR-028) | `contains`, POST | `contains`, GET + paginação | ✅ regra preservada; UI melhor |
| P-26 | Upload TACO (BR-023) | mapeamento fixo, trans = c52+c53 | idem + relatório e linhas inválidas ignoradas | 🔧 tratamento de erro |
| P-27 | Cadastro com chave (BR-024) | valida nome, senhas, chave | idem, mesmas mensagens | ✅ |
| P-28 | Trocar chave de cadastro (BR-025) | **quebrado** (`is_ajax`) | funciona, exige papel admin | 🔧 B1 corrigido |
| P-29 | Trocar senha de membro (BR-025) | **quebrado** (`is_ajax`) | funciona + validadores de senha | 🔧 B1 corrigido |
| P-30 | Excluir membro com transferência (BR-026) | **quebrado** (`is_ajax`) | funciona, mesma mensagem de contagem | 🔧 B1 corrigido |
| P-31 | Login e logout (BR-027) | logout ao abrir login; mensagem de falha | idem | ✅ |
| P-32 | Papel de administrador | `username == 'admin'` | grupo do Django | 🔧 B10 |
| P-33 | Exibir Biotina no rótulo | erro 500 | exibe | 🔧 B2 corrigido |
| P-34 | Ficha sem Tabela (16 do backup) | erro 500 | abre; cria a tabela | 🔧 B4 corrigido |
| P-35 | Ficha sem peso de porção (11 do backup) | erro 500 | exibe "0 porções" | 🔧 B15 corrigido |
| P-36 | Coluna 100 g do Manganês | mostrava o valor do Magnésio | mostra o próprio | 🔧 B3 corrigido |
| P-37 | Mutações por GET sem login | permitidas | exigem login + POST (405 no GET) | 🔧 B10 |
| P-38 | Registro inexistente | erro 500 | HTTP 404 | 🔧 |

## 3. Itens que exigem validação manual (🖐)

| ID | O que validar | Por quê | Como |
|----|---------------|---------|------|
| M-01 | Colar o rótulo no Google Docs e comparar com um rótulo emitido pelo sistema antigo | O conteúdo já é garantido por P-02/P-03 e a área de transferência foi verificada em navegador real (83 KB de `text/html` com tabelas, ingredientes, alérgicos e lupa), mas o resultado **visual colado** depende do Docs | Abrir a ficha → "Copiar conteúdo" → colar no Docs |
| M-02 | Conferir uma ficha nova contra planilha/cálculo manual | Confirma o pipeline com dados que não existem no backup | Criar ficha, comparar com a planilha de referência da equipe |
| M-03 | %VD do selênio (B9) e unidade da vitamina E | Divergem da IN 75/2020; **mantidos por decisão** (D-006) | Revisão de um nutricionista |
| M-04 | Importação TACO com o arquivo real usado pela equipe | O mapeamento de colunas é fixo e o arquivo de referência não está no repositório | Rodar o upload com o TXT real |

## 4. Cobertura

- **101 testes automatizados** (26 de domínio, 2 de paridade em massa, 73 de integração).
- Comandos para reproduzir:
  ```bash
  pytest                                                   # suíte completa
  PARIDADE_DB=<copia_do_backup> pytest tests/integration/test_paridade_rotulo_e2e.py
  ```
- Nenhuma funcionalidade do inventário (FEATURES.md, F-01..F-33) ficou sem implementação
  ou sem teste, exceto as marcadas 🖐 acima.
