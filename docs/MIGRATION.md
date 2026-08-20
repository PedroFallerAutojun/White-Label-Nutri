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

## 3. Preparação pós-restauração

O comando `sanear_backup`, que fazia estes passos de uma vez, foi removido na limpeza
de 17/08/2026. Não faz falta: o sistema resolve sozinho quase tudo o que ele fazia, e o
que sobrou é uma tela de configuração. Segue o que precisa acontecer e como acontece hoje.

| # | O que precisa acontecer | Como acontece hoje |
|---|---|---|
| S1 | As 16 fichas sem tabela (IDs 1138–1151, 2733, 2734) precisam abrir | **Automático.** `servicos.obter_tabela()` cria a tabela na primeira vez que a ficha é aberta |
| S2 | Alguém precisa administrar membros (chave, senhas, exclusão) | **Verificar.** Quem é superusuário já administra. Confira quem é superusuário (comando abaixo). Se ninguém for, rode `createsuperuser` |
| S3 | Conhecer fichas com data suspeita (2 no acervo: #98 em 2000, #5934 em 2006) | `manage.py auditar_tabelas` |
| S4 | Conhecer fichas sem peso de porção (11 no acervo) | Exibem "0 porções" em vez de erro; `auditar_tabelas` as lista |
| S5 | **NÃO** recalcular tabelas existentes | Nada recalcula sozinho. O recálculo é botão por ficha, na tela do rótulo (D-007/D-017) |
| S6 | Chave de cadastro | A vigente aparece na tela de Membros, para quem é administrador |
| S7 | **Criar a configuração da instância** | **Manual, e obrigatório** — veja abaixo |

Para conferir quem administra (S2):

```bash
python manage.py shell -c "from django.contrib.auth.models import User; print(list(User.objects.filter(is_superuser=True).values_list('username', flat=True)))"
```

### O passo que não pode ser esquecido (S7)

Depois de restaurar, entre em `/admin/` → **Configuração da instância** e crie a linha:

- **Nome da empresa:** `Nutri Jr`
- **Ano de corte de ingredientes:** `2024`
- Cor e logotipo, se a empresa quiser

Sem essa linha o sistema assume os padrões, e o mais grave é o ano de corte ficar vazio:
a lista de ingredientes volta a exibir a carga TACO de 2019, que a Nutri Jr esconde de
propósito (BR-017/D-010). Nada quebra — por isso passaria despercebido.

Para não depender da memória, o `manage.py check` avisa enquanto a configuração não
existir (`plataforma.W001`), e o aviso aparece também no deploy:

```
?: (plataforma.W001) Esta instância não tem configuração white-label.
   HINT: Crie em /admin/ → Configuração da instância ...
```

**Estado do acervo, medido em 2026-08-11:** as 1.574 fichas abrem sem erro (no sistema
original, 17 davam 500) e a paridade dos rótulos é 1.557/1.557.

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
