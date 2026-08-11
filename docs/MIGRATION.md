# Migração / Compatibilidade de Dados — White-Label-Nutri

## 1. Estratégia (D-003 — VALIDADA em runtime)

O banco antigo é usado **diretamente**: mesmo schema, mesmos IDs, mesmas senhas.
Validação executada em 2026-08-11 sobre cópia restaurada do `BackupNutriJR`:

- Restauração completa (schema + 17 tabelas + FKs + índices + sequences) sem erros.
- Integridade referencial comprovada (constraints aplicadas pós-carga com sucesso).
- Contagens conferem: 1.574 fichas, 1.558 tabelas, 8.042 itens, 2.052 ingredientes,
  99 membros, 101 usuários.
- O código original (Django 4.2.11) rodou sobre a cópia: telas principais 200 OK.

## 2. Restauração do backup

O `BackupNutriJR` é formato custom **v1.16** → requer `pg_restore` do PostgreSQL 17+:

```bash
cp BackupNutriJR /tmp/backup-copia          # NUNCA operar sobre o original
createdb nutri
pg_restore --no-owner --no-privileges -d nutri /tmp/backup-copia
```

Com client ≤16, usar o conversor somente-leitura (`scripts/` — parser do formato custom
que reconstrói schema_pre.sql + dados + schema_post.sql + seqs.sql), já testado.

## 3. Saneamento pós-restauração (idempotente, com log)

Executar UMA vez após restaurar, via comando de management `sanear_backup`:

| # | Ação | Motivo | Reversível |
|---|------|--------|-----------|
| S1 | Criar `Tabela` para as 16 fichas órfãs (IDs 1138–1151, 2733, 2734) com pk = ficha.pk e recalcular SOMENTE essas | B4 — hoje crasham (confirmado: DoesNotExist) | sim (delete) |
| S2 | Colocar o usuário `admin` no grupo "administradores" | modelo de permissão novo | sim |
| S3 | Sinalizar (não alterar) fichas com dataCriacao < 2019 (IDs com anos 2000/2006) | dados suspeitos | n/a |
| S4 | Sinalizar fichas com `pesoAnvisa` e `pesoPorcao` nulos (ex.: 1273 — crasha no original, B15) | a view nova exibirá aviso em vez de 500 | n/a |
| S5 | NÃO recalcular tabelas existentes | 45/50 divergem ao recalcular — os valores gravados são os rótulos emitidos (fonte de verdade histórica) | — |
| S6 | (opcional) manter apenas a última linha de `fichas_chave` | higiene | sim |

Log de execução gravado em tabela própria (`saneamento_log`) com timestamp e diff por ação.

## 4. Regra de ouro

- O arquivo `BackupNutriJR` original é **imutável** — toda operação usa cópia.
- Nenhuma migração destrutiva; migrations novas são aditivas.
- Antes de qualquer migração em produção: novo backup + ensaio em staging com
  a suíte de paridade (TESTING.md) verde.
