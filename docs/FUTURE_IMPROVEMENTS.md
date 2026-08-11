# Melhorias Futuras e Problemas Encontrados — Nutri Jr

Nada daqui deve ser implementado automaticamente. Prioridade do projeto:
**PARIDADE FUNCIONAL → ESTABILIDADE → UX → PERFORMANCE → NOVAS FUNCIONALIDADES.**

## Bugs no original (corrigir na nova versão COM decisão registrada em DECISIONS.md)

| # | Problema | Evidência | Efeito |
|---|----------|-----------|--------|
| B1 | `request.is_ajax()` (removido no Django 4.0) em mudaChave/trocaSenha/deletaMembro | views.py:1064/1085/1111 + Django 4.2.11 | **CONFIRMADO em runtime** (AttributeError): administração de membros quebrada (500) |
| B2 | `tabela.Biotina_Arred` (B maiúsculo) | views.py montarTabelaFinal | **CONFIRMADO em runtime**: exibir biotina → 500 |
| B3 | Linha Manganês usa `magnesio_100g` na coluna 100 g | views.py montarTabelaFinal | Valor errado no rótulo |
| B4 | 16 fichas sem Tabela no banco | backup (IDs 1138–1151, 2733, 2734) | **CONFIRMADO em runtime** (DoesNotExist): abrir essas fichas → 500 |
| B5 | `ing.save` sem parênteses em registrarIngrediente | views.py:1293 | Funciona por acidente (att100g salva) |
| B6 | Condição de zerar gordTotais usa `gordPoli` (total) na checagem por porção | views.py:390 | Assimetria porção × 100 g |
| B7 | `truncar` quebra com int/None | templatetags | 500 em casos raros |
| B8 | Reescrita de `_100g` com valor arredondado a cada attTabela | views.py:386 | Perda de precisão acumulada |
| B9 | selenio_VD referência 11 mg (IN 75/2020: 34 µg); vitaminaE unidade "mg" com referência "15 µg" no comentário | views.py:496/485 | %VD possivelmente errado — validar com nutricionista |
| B10 | Mutações via GET sem login/CSRF (F-13, F-18, F-19, F-23, F-06..08) | urls.py/views.py | Segurança |
| B11 | Filtro de busca ignora o corte ≥2024 da listagem | views.py:1214 vs 1227 | Inconsistência de UX |
| B12 | salvarReceita não recalcula a tabela | views.py:594 | Tabela desatualizada até o próximo recálculo |
| B13 | Editar ingrediente não recalcula fichas que o usam | views.py:1302 | Fichas antigas ficam defasadas (pode ser intencional — congelar fichas emitidas?) [VALIDAR] |
| B14 | Reset de senha (auth.urls) sem backend de e-mail | settings | Link "esqueci a senha" não funciona |
| B15 | `int(pesoAnvisa or pesoPorcao)` sem peso válido crasha fichaX | views.py (pesoAnvisaSemZero); 11 fichas no backup (ex.: 1273, com pesoAnvisa = 0) | **CONFIRMADO em runtime** (TypeError) → 500 |
| B16 | `attTabela` crasha com dados nulos (`float * None`) | 2 fichas do backup falham no recálculo | **CONFIRMADO em runtime** — novo cálculo trata None como 0 |
| B17 | Ordem dos ingredientes do rótulo é indefinida entre itens de MESMO peso (ORDER BY sem desempate) | views.py ordenarIngredientesPorQuantidade; 251/1557 fichas têm empates | Nova versão usa desempate estável (ordem de inserção); paridade validada por equivalência de grupos |

## Dívidas estruturais
- 335 colunas em `fichas_tabela` / ~100 em `fichas_ingrediente` → normalizar para
  tabela `nutriente(chave, valor…)` OU manter colunas por compatibilidade e encapsular
  em código com metadados (lista única de nutrientes com unidade, VD, ordem, seção).
- views.py com 449 KB (PNG base64 embutidos) → mover imagens para estáticos.
- Zero testes; criar suíte de paridade (golden files a partir do backup: para cada ficha,
  recalcular e comparar rótulo gerado com o do sistema antigo).
- Sem paginação/índices de busca; sem transações em attTabela (6 saves).
- Dois Bootstraps; jQuery apenas para 3 forms.
- Segredos: chave global em texto puro; sem níveis de permissão reais (username == 'admin').

## Ideias de produto (NÃO implementar sem aprovação)
- Exportar PDF/PNG do rótulo em vez de copiar HTML.
- Duplicar ficha; histórico/versões de ficha; busca global.
- ~~Multi-tenant/white-label~~ → **movido para o escopo do produto** (D-009). Ficam como
  evolução futura: billing/planos por empresa, subdomínio por tenant, cadastro
  self-service de organizações, isolamento físico (schema-per-tenant) para clientes
  que exigirem.
- Recalcular fichas em lote quando um ingrediente muda (com opção de congelar finalizadas).
- Suporte a alimentos líquidos nas lupas (limiares diferentes na RDC 429/2020).
