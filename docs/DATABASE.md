# Banco de Dados — Nutri Jr

## 1. Arquivos de backup encontrados [CONFIRMADO]

| Arquivo | Formato | Origem | Data | Conteúdo |
|---|---|---|---|---|
| `Nutri_Jr/BackupNutriJR` | pg_dump **custom v1.16** (pg_dump 17.6, servidor **PostgreSQL 17.9**, banco Heroku `demknq4tukrd65`) | Produção | **2026-06-18** | Backup ATUAL e completo |
| `Nutri_Jr/latest.dump` | pg_dump custom v1.13 (PG 11.6, banco `d9f4e81ogg83rp`) | Produção antiga | 2020-01-15 | Backup histórico (schema da época) |

⚠️ `BackupNutriJR` exige `pg_restore` do PostgreSQL **17+** (o formato v1.16 não é lido por
clients ≤16). A análise abaixo foi feita com um parser próprio somente-leitura
(TOC + descompressão zlib), sem alterar o arquivo original.

## 2. Estado do schema no backup [CONFIRMADO]

- As **10 migrations** do app `fichas` (0001…0010) estão aplicadas — o schema do backup é
  **idêntico** ao `models.py` atual. Nenhuma migração pendente.
- 17 tabelas: 7 do app `fichas` + 10 do Django (auth_*, django_*).
- Django 4.2 + `django.contrib.auth` padrão (senhas PBKDF2 em `auth_user`).

## 3. Volumetria (backup 2026-06-18) [CONFIRMADO]

| Tabela | Linhas | Observação |
|---|---:|---|
| fichas_ficha | 1.574 | fichas de 2019 a 2026 (2 com datas erradas: 2000, 2006) |
| fichas_tabela | 1.558 | **16 fichas órfãs sem tabela** (IDs 1138–1151, 2733, 2734) |
| fichas_ficha_ingrediente | 8.042 | itens de receita |
| fichas_ingrediente | 2.052 | inclui carga TACO 2019 + manuais |
| fichas_membro | 99 | |
| auth_user | 101 | 99 membros + admin + extras |
| fichas_nutriente | 0 | nutrientes extras manuais (recurso pouco usado) |
| fichas_chave | 1 | chave global de cadastro (texto puro) |
| django_admin_log / django_session | 735 / 742 | histórico/sessões |

## 4. Modelo lógico (ERD)

```
auth_user 1──1 fichas_membro
                   │ 1                         │ 1
                   │                           │
                   ▼ N                         ▼ N
            fichas_ingrediente          fichas_ficha ──1──1── fichas_tabela ──1──N── fichas_nutriente
                   │ N                         │ 1                (origem_id UNIQUE,      (origemTabela_id)
                   │                           │                   pk == ficha.pk por
                   └────► fichas_ficha_ingrediente ◄───┘            convenção da aplicação)
                          (N↔N com atributos: pesoBruto,
                           pesoLiquido, medidaCaseira, nomeFantasia)

fichas_chave (isolada — 1 linha, chave de cadastro)
```

### Tabelas do domínio

**fichas_membro** — Objetivo: perfil do usuário. PK `id`; FK/UNIQUE `usuario_id → auth_user.id`.
Colunas: nome (120), semestre (6), email (254). Usada por: Ficha.autor, Ingrediente.autorIng.
`on_delete=CASCADE` a partir de User.

**fichas_ingrediente** — Objetivo: composição nutricional de um ingrediente para `qtdeDoIngrediente`
gramas (default 100). PK `id`; FK `autorIng_id → membro`. ~100 colunas: nomeIng, composicao (250,
usada na lista de ingredientes do rótulo), origemDosDados, addManualmente, numRef, dataCriacao,
qtdeDoIngrediente + **46 pares nutriente / nutriente_100g** (double precision).
Regra: `_100g = valor*100/qtdeDoIngrediente`, recalculado por `att100gIngrediente()`.

**fichas_ficha** — Objetivo: cabeçalho da ficha técnica. PK `id`; FK `autor_id → membro`.
Colunas: cliente, nomeFicha (500), dataCriacao, finalizada (bool), pesoLiquidoPreparacao (soma
calculada), pesoTotal (informado), pesoPorcao (porção "cliente"), pesoAnvisa (porção ANVISA),
numPorcoes (int, calculado), medCaseiraPorcao.

**fichas_ficha_ingrediente** — Objetivo: item da receita (N↔N Ficha×Ingrediente com atributos).
PK `id`; FKs `ficha_id`, `ingrediente_id` (CASCADE). Colunas: pesoBruto, pesoLiquido (base de
TODOS os cálculos), medidaCaseira (30), nomeFantasia (50 — nome exibido no rótulo).

**fichas_tabela** — Objetivo: tabela nutricional calculada e persistida da ficha (cache
materializado). PK `id` (== ficha.pk por convenção); FK/UNIQUE `origem_id → ficha`.
335 colunas: informacoesComplementares (text) + 46 nutrientes × colunas
`X`, `X_100g`, `X_Porcao`, `X_Arred`, `X_VD` (int), `X_Mostrar` (bool), `X_unidadeMd` (varchar 5).
Defaults de `_Mostrar`: true só para o obrigatório ANVISA (proteínas, gorduras totais/sat/trans,
carboidratos, fibras, energia kcal/kJ, sódio, açúcares totais/adicionados); resto false.

**fichas_nutriente** — Objetivo: linha extra manual na tabela final. PK `id`;
FK `origemTabela_id → tabela` (CASCADE). Colunas: nomeNutri, qtde, qtde_Arred, qtde_VD, medida.

**fichas_chave** — Objetivo: chave global de auto-cadastro. PK `id`; key (20). A aplicação usa
`Chave.objects.last()`; trocas de chave INSEREM nova linha.

### Constraints e índices [CONFIRMADO no dump]
- PKs em todas; UNIQUEs: `fichas_membro.usuario_id`, `fichas_tabela.origem_id`.
- FKs `DEFERRABLE INITIALLY DEFERRED` (padrão Django/PG).
- Índices btree nas FKs. Sem soft delete, sem campos de auditoria (além de dataCriacao),
  sem enums no banco.

## 5. Compatibilidade com a nova versão

**Decisão recomendada: usar o banco antigo DIRETAMENTE (opção A).**

- O schema é limpo, com FKs íntegras (validado: nenhuma FK quebrada nas 8.042 linhas de
  ficha_ingrediente; tabelas órfãs não existem — só fichas sem tabela).
- Se a nova versão for Django, basta apontar para um banco restaurado do backup e aplicar
  migrations novas **aditivas**. IDs preservados automaticamente.
- Senhas dos 101 usuários são hashes padrão Django (PBKDF2) → login continua funcionando se
  a nova auth for compatível com esse formato de hash.

Pontos que a nova versão deve tratar na importação/normalização (processo reprodutível,
idempotente e com log — nunca sobre o arquivo original):

1. Criar as 16 `Tabela` faltantes (fichas 1138–1151, 2733, 2734) e recalcular.
2. Corrigir/normalizar `dataCriacao` absurdas (2000, 2006) — sinalizar, não apagar.
3. Opcional: consolidar `fichas_chave` para 1 linha.
4. `numPorcoes` persistido pode estar desatualizado (fórmula mudou — o código atual recalcula
   na exibição); recalcular na importação.
5. Restauração requer PostgreSQL 17+ (`pg_restore` 17+). Comando de referência:
   `createdb nutri && pg_restore --no-owner --no-privileges -d nutri BackupNutriJR` (sempre
   sobre uma CÓPIA do arquivo).

## 6. Riscos
- Colunas double precision acumulam ruído de ponto flutuante (valores como
  1.0000000000000002 existem no backup) — a paridade de cálculo deve comparar com tolerância.
- O modelo de 335 colunas é hostil a evolução; qualquer normalização futura exige migração
  cuidadosa com testes de paridade (ver TESTING futuro).
