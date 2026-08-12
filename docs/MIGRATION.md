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
| S4 | Sinalizar fichas sem peso de porção — nulo **ou zero** (11 fichas no backup: 272, 771, 774, 1141, 1273, 1415, 1423, 1486, 4659, 5736, …) | B15: exibem “0 porções” em vez de erro 500 | n/a |
| S5 | NÃO recalcular tabelas existentes | 45/50 divergem ao recalcular — os valores gravados são os rótulos emitidos (fonte de verdade histórica) | — |
| S6 | (opcional) manter apenas a última linha de `fichas_chave` | higiene | sim |
| S7 | Criar `ConfiguracaoInstancia` da instância Nutri Jr (`nome_exibicao="Nutri Jr"`, `ano_corte_ingredientes=2024`, D-010) | D-009 — instância por empresa | sim |

O comando `sanear_backup` implementa S1–S7, relata cada ação no terminal e aceita
`--dry-run` para simular sem gravar. É idempotente (a segunda execução é um no-op).

```bash
python manage.py sanear_backup --dry-run    # relatório
python manage.py sanear_backup             # aplica
```

**Execução validada sobre a cópia do backup (2026-08-11):**
- S1: criadas as 16 tabelas faltantes (fichas 1138–1151, 2733, 2734);
- S2: usuário `admin` promovido ao grupo `administradores`;
- S3: 2 fichas com data anterior a 2019 sinalizadas (#98 em 2000, #5934 em 2006) — não alteradas;
- S4: 11 fichas sem peso de porção sinalizadas;
- S7: configuração da instância criada (Nutri Jr, corte 2024).

Resultado: **as 1.574 fichas do acervo abrem sem erro** (no original, 17 davam 500) e a
paridade dos rótulos permanece 1.557/1.557 — o saneamento não altera nenhum rótulo existente.

## 3b. Provisionar uma empresa nova (D-009)

```bash
createdb nutri_acme && DATABASE_URL=... python manage.py migrate
DATABASE_URL=... python manage.py bootstrap_instancia \
    --nome "Nutri Acme" --admin ana --email ana@acme.com --chave ACME-2026
```
Cria a configuração white-label, o grupo de administradores, o primeiro administrador
(com Membro correspondente) e a chave de cadastro. A senha vem de `--senha`, da variável
`INSTANCIA_ADMIN_SENHA` ou é solicitada interativamente. Recusa rodar se a instância já
estiver configurada.

## 4. Regra de ouro

- O arquivo `BackupNutriJR` original é **imutável** — toda operação usa cópia.
- Nenhuma migração destrutiva; migrations novas são aditivas.
- Antes de qualquer migração em produção: novo backup + ensaio em staging com
  a suíte de paridade (TESTING.md) verde.
