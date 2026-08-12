# Engenharia Reversa — Nutri Jr (sistema original)

> Documento-mestre da análise do sistema original (repositório `Nutri_Jr`).
> Documentos complementares: [DATABASE.md](DATABASE.md), [BUSINESS_RULES.md](BUSINESS_RULES.md),
> [FEATURES.md](FEATURES.md), [FLOWS.md](FLOWS.md), [UI.md](UI.md),
> [FUTURE_IMPROVEMENTS.md](FUTURE_IMPROVEMENTS.md), [DECISIONS.md](DECISIONS.md).
>
> Classificação das informações: **[CONFIRMADO]** = lido no código/banco; **[PROVÁVEL]** = inferido
> com alta confiança; **[PRECISA SER VALIDADO]** = requer execução do sistema ou confirmação do usuário.

## 1. Visão geral

O **Nutri Jr** é um sistema web interno da empresa júnior de Nutrição ("Nutri Jr") para produzir
**fichas técnicas de preparação** e **tabelas nutricionais rotuláveis** conforme as normas da
ANVISA (RDC 429/2020 e IN 75/2020), incluindo a **rotulagem nutricional frontal** (as "lupas"
de ALTO EM açúcar adicionado / gordura saturada / sódio).

Fluxo central: o membro cadastra **ingredientes** (com composição nutricional por N gramas),
monta uma **ficha** (receita = lista de ingredientes com pesos), e o sistema calcula
automaticamente a **tabela nutricional** (por porção, por 100 g, %VD, arredondamento ANVISA),
gerando uma página final formatada para ser copiada para o Google Docs (modelo vertical e linear).

- Usuários: membros da empresa júnior (~99 membros no backup). Cadastro protegido por uma
  **chave global** compartilhada. Não há níveis de permissão além do usuário `admin` (por username).
- Produção: Heroku (`sistema-nutrijr.herokuapp.com`), PostgreSQL 17.9. **[CONFIRMADO]**

## 2. Stack identificada [CONFIRMADO]

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.12.1 (`runtime.txt`) |
| Framework | Django 4.2.11 (monólito server-rendered, function-based views) |
| Banco (prod) | PostgreSQL (Heroku Postgres; backup atual dumped do PG 17.9) |
| Banco (dev) | PostgreSQL local (settings/dev.py; era SQLite segundo o README) |
| Front-end | Django Templates + Bootstrap 3.3.7 **e** 4.3.1 via CDN (ambos carregados!), Font Awesome 4.7, jQuery (AJAX na tela de membros), CSS próprio em `assets/fichas/*.css` |
| Servidor | gunicorn + WhiteNoise (estáticos) |
| Deploy | Heroku (`Procfile`: `release: migrate`, `web: gunicorn`), django-heroku, dj-database-url |
| Formulários | django-bootstrap-form 3.4 |
| Dependências | Pillow, psycopg2-binary, pytz, sqlparse, whitenoise, setuptools |

Não existem: testes automatizados (tests.py vazio), API REST, jobs em background, cache,
e-mails transacionais (variáveis EMAIL_* definidas mas sem uso no código), geração de PDF
(a "exportação" é copiar HTML para o clipboard), uploads de imagem. **[CONFIRMADO]**

## 3. Estrutura do projeto original [CONFIRMADO]

```
Nutri_Jr/
├── BackupNutriJR          # pg_dump custom v1.16 (PG 17.9) de 2026-06-18 — banco de PRODUÇÃO
├── latest.dump            # pg_dump custom v1.13 (PG 11.6) de 2020-01-15 — backup antigo
├── Procfile, runtime.txt, requirements.txt
├── manage.py              # aponta para nutri.settings.dev (trocado manualmente p/ prod no deploy)
├── nutri/
│   ├── settings/ (base.py, dev.py, prod.py)
│   ├── urls.py            # todas as 24 rotas do sistema
│   └── wsgi.py
├── fichas/                # ÚNICO app Django (todo o domínio)
│   ├── models.py          # 7 models
│   ├── views.py           # 25 views/funções (449 KB — contém 7 PNGs base64 das lupas ANVISA)
│   ├── forms.py           # 12 forms
│   ├── admin.py           # registro simples dos 7 models
│   ├── templatetags/trunca_numeros.py
│   ├── migrations/ (0001..0010)
│   └── templates/ (14 templates)
├── assets/fichas/*.css    # 13 arquivos CSS (1 por tela, aproximadamente)
└── staticfiles/           # coletados (gerados)
```

## 4. Módulos funcionais

1. **Autenticação** — login/logout próprios (username+senha via `django.contrib.auth`).
2. **Membros** — cadastro com chave global, listagem, troca de chave (admin), troca de senha
   de qualquer usuário (admin), exclusão de membro com transferência de autoria (admin).
3. **Ingredientes** — CRUD + filtros + upload em lote de arquivo TXT (TACO, separado por TAB).
4. **Fichas** — wizard de 3 passos (dados base → receita → tabela final) + visualização/rotulagem,
   marcação de finalizada, exclusão.
5. **Tabela nutricional** — cálculo automático (soma da receita → 100 g → porção → arredondamento
   ANVISA → %VD), seleção do que aparece na versão final, nutrientes extras manuais,
   informações complementares.
6. **Rotulagem final (fichaX)** — tabela vertical + linear, lista de ingredientes ordenada por peso,
   lupas ANVISA, cópia formatada para Google Docs.
7. **Ajuda** — página estática de instruções.

## 5. Autenticação e autorização [CONFIRMADO]

- Sessões Django padrão. `@login_required(login_url='loginUser')` na maioria das views.
- **Views SEM `@login_required`** (acessíveis deslogado — comportamento a decidir se preserva):
  `deletarItemReceita`, `editarItemReceita`, `salvarReceita`, `deletarNutrienteExtra`,
  `atualizarMostrar`, `atualizarFinalizada`, `mudaChave`, `trocaSenha`, `deletaMembro`,
  `registrarMembro` (este último é intencional — auto-cadastro com chave).
- "Admin" = `request.user.username == 'admin'` (hardcoded). Só ele vê a chave e os formulários
  de administração de membros na tela de membros — mas as views AJAX em si não verificam
  ser admin (fragilidade).
- Cadastro exige a **chave** global (model `Chave`, usa `Chave.objects.last()`).
- Django admin nativo habilitado em `/admin/`.

## 6. Integrações e dependências externas

- **Heroku** (deploy, env vars: `SECRET_KEY`, `DEBUG`, `DATABASE_URL`, `EMAIL_HOST_*` sem uso).
- **CDNs**: Bootstrap 3 e 4, Font Awesome, jQuery. Sem chamadas a APIs de terceiros.
- **TACO/IBGE**: dados nutricionais entram por upload de TXT exportado do Excel (offline).

## 7. Pontos frágeis e problemas identificados

Ver lista completa com evidências em [FUTURE_IMPROVEMENTS.md](FUTURE_IMPROVEMENTS.md). Destaques:

1. **`request.is_ajax()` removido no Django 4.0** é usado em `mudaChave`, `trocaSenha` e
   `deletaMembro` (views.py:1064, 1085, 1111). Com Django 4.2.11 do requirements, essas três
   funções de administração devem lançar `AttributeError` (500). **[PROVÁVEL — validar em produção]**
2. **Bug `Biotina_Arred`** (maiúscula) em `montarTabelaFinal` (views.py:~950): exibir Biotina na
   tabela final crasha a fichaX. **[CONFIRMADO no código]**
3. **Copy-paste bug**: linha "Manganês" da tabela final mostra o valor de `magnesio_100g`
   na coluna 100 g. **[CONFIRMADO]**
4. **16 fichas órfãs no backup** (IDs 1138–1151, 2733, 2734) sem `Tabela` correspondente —
   abrir qualquer uma delas gera `Tabela.DoesNotExist` (500). **[CONFIRMADO no backup]**
5. Convenção implícita **`Tabela.pk == Ficha.pk`** criada manualmente em `registrarFichaBase`;
   várias views buscam `Tabela.objects.get(pk=pk_da_ficha)` em vez de `origem=ficha`.
6. `DEBUG = 'True'` (string, sempre truthy) em base.py; SECRET_KEY antiga comentada no código;
   senha/chave global em texto puro na tabela `fichas_chave`.
7. Sem CSRF/permissão nas views de mutação por GET (`atualizarMostrar`, `deletarItemReceita`,
   `atualizarFinalizada` etc.) — mutações via GET.
8. `trunca_numeros.truncar` quebra com valores inteiros/None (assume que sempre há `.`).
9. ~46 nutrientes × 7 colunas modelados como **colunas repetidas** em `Tabela` (335 colunas) e
   `Ingrediente` (~100 colunas) — o motivo do código gigante e repetitivo.
10. `attTabela` faz 6 `save()` completos por chamada (sem transação explícita).
11. Filtro oculto `dataCriacao__year >= 2024` esconde ingredientes antigos da lista e da receita
    (regra de negócio intencional? **[PRECISA SER VALIDADO]** com o usuário).
12. Dois Bootstraps (3 e 4) carregados juntos; CSS conflitante.

## 8. Comportamentos que PRECISAM ser preservados

- Todo o pipeline de cálculo nutricional e arredondamento ANVISA (ver BUSINESS_RULES.md,
  BR-001 a BR-014) — é o coração do sistema.
- Regras das lupas "ALTO EM" e suas 7 combinações de imagem.
- Formato de exibição: tabela vertical + linear, seções com traços, itens indentados,
  "Não contém quantidades significativas de …" (informações complementares), formato
  "Cerca de N porções" / frações de porção.
- Cópia formatada para Google Docs (a saída real do trabalho dos membros).
- Cadastro por chave global; administração de membros com transferência de autoria.
- Upload TACO com o mapeamento de colunas atual.
- Compatibilidade com os dados do backup (IDs preservados; ver DATABASE.md §5).
- Convenção Tabela.pk == Ficha.pk enquanto o banco antigo for usado diretamente.

## 9. Funcionalidades que não podem ser perdidas

Inventário completo em [FEATURES.md](FEATURES.md) — 33 funcionalidades mapeadas (F-01 a F-33).
