# Estratégia de Testes e Paridade — White-Label-Nutri

## 1. Golden dataset (JÁ GERADO — `tests/golden/golden_fichax.json.gz`)

Capturado em 2026-08-11 executando o **código original** sobre a cópia restaurada do
`BackupNutriJR`: para cada ficha, o contexto exato que a view `fichaX` envia ao template
(a "verdade" do rótulo). **1.557 fichas** capturadas; 17 registradas com erro
(16 órfãs + ficha 1273 com pesos nulos).

Formato por ficha (`fichas[<id>]`):
```json
{
  "nomeFicha": "...", "cliente": "...", "finalizada": false,
  "pesoAnvisaSemZero": 100,           // peso da porção exibido (int, sem ,0)
  "numPorcoesExibicao": "Cerca de 7 porções",  // BR-011
  "numPorcoes": 0,                    // recalculado na exibição (BR-010)
  "medCaseiraPorcao": "...",
  "ordemIngredientes": "Farinha de trigo, óleo de soja, ...",  // BR-014
  "lupa": "4e42155fdfe8" | null,      // sha1[:12] do base64 da imagem (BR-012)
  "infComplementares": "...",
  "linhas": [["Valor energético", "151", 7, "kcal", 151], ...]
        // [rótulo, valor_porção_formatado, %VD ("" p/ açúcares totais), unidade, valor_100g]
        // linhas de nutrientes extras têm 3 posições
}
```

Mapa `lupa` → combinação: `0c869dc433ff` açúcares+gorduras+sódio · `041acba626cf`
açúcares+gorduras · `93fc9d989dcc` açúcares+sódio · `ee92eb2a1dde` gorduras+sódio ·
`47a278f93e77` açúcares · `4e42155fdfe8` gorduras · `f82c1af3f876` sódio.
Distribuição no backup: sem lupa 1.000 · gorduras 339 · sódio 106 · açúcares+gorduras 72 ·
gorduras+sódio 27 · açúcares 13.

### Teste de paridade principal
Para cada ficha do golden: a nova implementação, lendo o MESMO banco restaurado,
deve produzir linhas, lupa, porções e lista de ingredientes **idênticos**
(comparação exata de strings formatadas; floats intermediários com tolerância 1e-9).
Meta: 1.557/1.557. Exceções permitidas apenas para bugs corrigidos com decisão
registrada (ex.: B3 Manganês — o golden carrega o valor errado do original; o teste
marca essas linhas como `xfail-corrigido`).

## 2. Testes unitários do domínio (BR-001..BR-030)
- `arredondamento`: tabela de casos do round_half_down e faixas ANVISA (BR-006),
  limites de zero (BR-007) — incluindo os casos de borda 0.5/4/17/5/0.2.
- `calculo`: soma da receita, Atwater, /100g, /porção com fallback pesoAnvisa→pesoPorcao,
  %VD com todas as referências (BR-008), nutrientes sem VD.
- `rotulo`: formatação tira_zero/vírgula, açúcares totais sem VD, indentação,
  fatiamento das seções (BR-030), porções em frações (BR-011 — casos: exato, >3,
  ≤3 com ¼/½/¾, singular/plural, zero).
- `lupas`: 8 combinações (BR-012), limiares exatos (15/6/600 por 100 g).

## 3. Testes de integração (views + banco)
- Wizard completo (FL-01) com asserções no banco após cada passo.
- Regras de guarda: último item da receita (BR-018), pesoTotal/pesoPorcao ≠ 0 (BR-016),
  nome de ingrediente duplicado (BR-022), chave incorreta (BR-024), origem≠destino (BR-026).
- Autorização: rotas exigem login; ações admin exigem papel; mutações só por POST.
- Upload TACO: arquivo de amostra com colunas reais, incluindo gordTrans = c52+c53.

## 4. Testes de migração/saneamento
- `sanear_backup` idempotente (2ª execução = no-op) sobre fixture derivada do backup.
- S1: as 16 fichas órfãs abrem sem erro após saneamento.
- Restauração ponta a ponta em CI com PostgreSQL 17 (quando disponível).

## 5. Regressão visual/cópia (Etapa J)
- Snapshot do HTML do bloco copiável do rótulo (estrutura, não estilo).
- Teste manual roteirizado: colar no Google Docs e comparar com um rótulo emitido real.

## 6. Como regenerar o golden
Script `scripts/gera_golden.py` (porta do usado na Etapa C): restaurar cópia do backup,
apontar o código ORIGINAL para ela e capturar o contexto de fichaX com monkeypatch de
`render`. Nunca regenerar a partir do código novo (perderia o valor de oráculo).
