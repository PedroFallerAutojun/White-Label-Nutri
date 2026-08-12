# Fluxos Principais — Nutri Jr

## FL-01 — Criar ficha completa (fluxo feliz)
```
Login → Lista de Fichas → "Nova ficha"
 → Passo 1 (dados base) [POST válido]
    → cria Ficha + Tabela(pk=ficha.pk)                     (BR-015)
 → Passo 2 (receita): para cada ingrediente:
    digita nome (datalist ≥2024) + pesos + medida + fantasia [POST]
    → valida pesoTotal≠0 e pesoPorcao≠0                    (BR-016)
    → busca ingrediente por nome exato
       ├─ não existe → flash "Ingrediente ... não foi encontrado"
       └─ existe → cria Ficha_Ingrediente → attTabela():
            soma nutrientes (BR-002) → Atwater (BR-003) → /100g (BR-004)
            → /porção (BR-005) → zeros+arredonda (BR-006/007) → %VD (BR-008)
            → pesoLiquidoPreparacao, numPorcoes (BR-010) [6 saves]
 → Passo 3: toggles de exibição (F-19), nutrientes extras (F-17),
    informações complementares [POST] → fichaX
 → fichaX: monta rótulo (BR-009..BR-014, BR-030), lupas (BR-012)
 → "Copiar tudo" → cola no Google Docs
 → "Marcar como finalizada" (BR-021)
```

## FL-02 — attTabela (recálculo — chamado por: editar base, adicionar item,
remover item, abrir edição de item)
```
resetaNutrientes(0) → soma receita → Atwater → soma pesoLiquido
→ _100g (usa ficha.pesoTotal; 0 se ausente) → _Porcao (pesoAnvisa||pesoPorcao)
→ _Arred + REESCRITA de _100g arredondado (BR-006 ⚠) → ficha.numPorcoes
→ _VD (sobre _Arred)
```
⚠ Fluxos que NÃO recalculam: salvarReceita (edição de item), editar ingrediente
(fichas que o usam ficam desatualizadas até o próximo attTabela da ficha).

## FL-03 — Cadastro de membro
```
/registrarMembro (deslogado forçado)
 → POST: username livre? senhas iguais? chave == Chave.last()?
    ├─ falha → flash específico, permanece na tela
    └─ ok → cria User + Membro → redirect listaFichas (cai no login pois não autentica)
```

## FL-04 — Administração de membros (admin)
```
/listaMembros → (admin) vê chave + 3 forms AJAX
 ├─ mudaChave: INSERT nova Chave → JSON {nova_chave}
 ├─ trocaSenha: make_password → salva no User → JSON
 └─ deletaMembro: valida origem≠destino → transfere fichas+ingredientes → deleta User
     └─ CASCADE deleta Membro; JSON com contagens
⚠ os três usam request.is_ajax() — removido no Django 4+; hoje devem falhar (500).
```

## FL-05 — Upload TACO
```
/upload [GET] → form
/upload [POST]: valida extensão .txt → decode utf-8 → pula cabeçalho
 → para cada linha TAB: update_or_create Ingrediente (mapeamento fixo, BR-023)
 → att100gIngrediente para TODOS os ingredientes do banco
 → renderiza a mesma página (sem resumo do resultado)
Erros: linha malformada → exceção 500 (sem tratamento) [CONFIRMADO]
```

## FL-06 — Fluxos de erro conhecidos
- Ficha sem Tabela (16 no backup) → fichaX/passo2/passo3 → DoesNotExist → 500.
- Biotina marcada como mostrar → AttributeError em montarTabelaFinal → 500.
- listaFichas tem try/except com log (único endpoint com tratamento explícito).
- Acesso deslogado a rotas protegidas → redirect login. Rotas ⚠ (F-13..F-15, F-18, F-19,
  F-23, F-06..F-08) executam mesmo deslogadas.
- Registro inexistente em qualquer `objects.get(pk=…)` → 500 (sem get_object_or_404,
  apesar de importado).
```
