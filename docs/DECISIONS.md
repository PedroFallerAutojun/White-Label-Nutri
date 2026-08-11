# Registro de Decisões — Novo Nutri Jr (White-Label-Nutri)

| ID | Data | Decisão | Status |
|----|------|---------|--------|
| D-001 | 2026-08-11 | O repositório original `Nutri_Jr` é somente fonte de engenharia reversa; nenhuma alteração será feita nele. Toda a nova implementação vive em `White-Label-Nutri`. | Ativa |
| D-002 | 2026-08-11 | O backup `BackupNutriJR` nunca é modificado; qualquer análise/restauração usa cópias. Restauração requer PostgreSQL 17+. | Ativa |
| D-003 | 2026-08-11 | Compatibilidade de dados: usar o banco antigo diretamente (mesmos nomes de tabelas/colunas e IDs preservados), com migrations apenas aditivas + rotina de saneamento (fichas órfãs, numPorcoes defasado). Ver DATABASE.md §5. | Proposta — aguarda validação |
| D-004 | — | Stack da nova versão (a definir na fase de planejamento; White-Label-Nutri está vazio, sem stack pré-existente). | Pendente |
| D-005 | — | Destino dos bugs B1–B14 (preservar comportamento vs corrigir) — decidir um a um na especificação da nova versão. | Pendente |
| D-006 | — | Confirmar com o usuário: filtro de ingredientes ≥2024 (BR-017), %VD de selênio (B9), recálculo de fichas ao editar ingrediente (B13), escopo "white-label". | Pendente |
