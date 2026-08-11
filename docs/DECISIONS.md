# Registro de Decisões — Novo Nutri Jr (White-Label-Nutri)

| ID | Data | Decisão | Status |
|----|------|---------|--------|
| D-001 | 2026-08-11 | O repositório original `Nutri_Jr` é somente fonte de engenharia reversa; nenhuma alteração será feita nele. Toda a nova implementação vive em `White-Label-Nutri`. | Ativa |
| D-002 | 2026-08-11 | O backup `BackupNutriJR` nunca é modificado; qualquer análise/restauração usa cópias. Restauração requer PostgreSQL 17+. | Ativa |
| D-003 | 2026-08-11 | Compatibilidade de dados: usar o banco antigo diretamente (mesmos nomes de tabelas/colunas e IDs preservados), com migrations apenas aditivas + rotina de saneamento (fichas órfãs, numPorcoes defasado). Ver DATABASE.md §5 e MIGRATION.md. | **Validada em runtime** (2026-08-11): backup restaurado em cópia, FKs íntegras, código original rodou sobre ela |
| D-004 | 2026-08-11 | Stack da nova versão: **Django 5.2 LTS + PostgreSQL + Bootstrap 5 + htmx + pytest** (proposta detalhada em NEW_ARCHITECTURE.md — reaproveita auth/senhas/schema do banco antigo). | Proposta — aguarda aprovação |
| D-005 | 2026-08-11 | Bugs B1–B15: **corrigir** na nova versão. Exceções (por D-006): B9 e B13 mantidos. B6/B8 (regras de cálculo) corrigidos apenas para fichas novas/recalculadas, nunca em massa (ver NEW_ARCHITECTURE.md §3.5). | Ativa (decidido pelo usuário) |
| D-006 | 2026-08-11 | **Manter** comportamentos: filtro de ingredientes ≥2024 (BR-017), %VD de selênio 11 mg (B9), sem recálculo retroativo ao editar ingrediente (B13), escopo atual (sem multi-tenant). | Ativa (decidido pelo usuário) |
| D-007 | 2026-08-11 | Valores persistidos de `fichas_tabela` são a fonte de verdade histórica (rótulos emitidos): a importação NÃO recalcula tabelas existentes. Motivo: recalcular diverge em 45/50 fichas testadas (ingredientes/regras mudaram após a última edição). | Ativa |
| D-008 | 2026-08-11 | Paridade é verificada contra o golden dataset `tests/golden/golden_fichax.json.gz` (1.557 fichas, gerado do código ORIGINAL sobre o backup). Meta: reprodução idêntica, exceto bugs corrigidos com registro. | Ativa |
