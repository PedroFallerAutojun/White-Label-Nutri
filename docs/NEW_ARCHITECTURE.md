# Arquitetura da Nova Versão — White-Label-Nutri

> Proposta da Etapa D (planejamento). Depende da aprovação de **D-004** em DECISIONS.md.
> Princípio regente: **paridade funcional primeiro** (ver docs/TESTING.md), melhorias depois.

## 1. Stack proposta

| Camada | Escolha | Justificativa |
|---|---|---|
| Linguagem | Python 3.12+ | continuidade com o domínio já validado |
| Framework | **Django 5.2 LTS** | (a) o banco antigo é um schema Django com `auth_user` e hashes de senha PBKDF2 — login dos 101 usuários continua funcionando sem migração; (b) migrations/admin de graça; (c) equipe já conhece o modelo mental; (d) SPA não traria ganho para um sistema interno server-rendered |
| Banco | PostgreSQL 16+ (mesmo schema do backup) | decisão D-003 validada em runtime |
| Front-end | Django Templates + **Bootstrap 5** + htmx (interações pontuais: filtros, toggles da tabela, autocomplete) | elimina jQuery e os dois Bootstraps; mantém server-rendered |
| Testes | pytest + pytest-django + golden files | ver TESTING.md |
| Deploy | mesmo modelo Heroku (Procfile, gunicorn, WhiteNoise) — portável para outros PaaS | menor atrito de operação |
| Config | django-environ (12-factor, sem trocar manage.py na mão) | corrige o fluxo de deploy manual dev↔prod |

## 2. Estrutura do projeto

```
White-Label-Nutri/
├── config/                    # settings (base/dev/prod via env), urls, wsgi
├── apps/
│   ├── plataforma/            # ConfiguracaoInstancia (branding, ano_corte) — app NOVO
│   └── fichas/                # app de domínio — label `fichas` PRESERVADO (D-012),
│       ├── models/            #   membro.py, ingrediente.py, ficha.py, tabela.py...
│       ├── views/             #   auth.py, membros.py, ingredientes.py, fichas.py, rotulo.py
│       └── dominio/           # NÚCLEO PURO (sem Django):
│           ├── nutrientes.py  #   registro único dos 46 nutrientes (metadados)
│           ├── calculo.py     #   BR-001..BR-008 como funções puras
│           ├── arredondamento.py  # BR-006/BR-007 (round_half_down, ANVISA)
│           ├── rotulo.py      #   BR-009..BR-014, BR-030 (montagem das linhas)
│           └── lupas.py       #   BR-012
├── templates/ · static/
├── tests/
│   ├── unit/                  # regras BR-*
│   ├── integration/           # views + banco
│   └── golden/                # dataset de paridade (já gerado)
├── scripts/                   # restauração de backup, saneamento (MIGRATION.md)
└── docs/
```

## 3. Decisões estruturais chave

### 3.1 Registro único de nutrientes (mata a repetição 46×)
Um metadado por nutriente substitui os 7 blocos repetidos por nutriente do original:

```python
@dataclass(frozen=True)
class NutrienteDef:
    chave: str            # "proteinas" — igual ao prefixo das colunas do banco
    rotulo: str           # "Proteínas"
    unidade: str          # "g" | "mg" | "μg" | "kcal" | "kJ"
    vd_referencia: float | None   # None = %VD em branco/zerado (BR-008/BR-009)
    limite_zero_porcao: float | None  # BR-007
    limite_zero_100g: float | None
    mostrar_padrao: bool
    secao: int            # ordem/agrupamento no rótulo (BR-030)
    indentado: bool
NUTRIENTES: tuple[NutrienteDef, ...]  # 46 entradas — única fonte de verdade
```
Models, cálculo, rótulo, formulários e templates iteram sobre esse registro.
As colunas do banco permanecem as mesmas (compatibilidade), acessadas via
`getattr(tabela, f"{n.chave}_Arred")` encapsulado num repositório.

### 3.2 Cálculo como função pura + persistência explícita
`calcular_tabela(ficha, itens) -> ResultadoTabela` reproduz `attTabela` passo a passo
(mesma ordem, mesmos efeitos, incluindo a reescrita de `_100g` arredondado — B8 preservado
por padrão para paridade; correção fica atrás de flag até validação com fichas novas).
Uma única transação, um único `save()` (vs 6 do original).

### 3.3 Compatibilidade de modelos
Models novos com `class Meta: db_table = "fichas_ficha"` etc. e `db_column` idênticos,
`AutoField` (não BigAutoField) para casar com o schema. Estado inicial de migrations
aplicado com `--fake-initial` sobre o banco restaurado. Invariante `Tabela.pk == Ficha.pk`
mantido (BR-015) enquanto o schema antigo for o vigente.

### 3.4 Autenticação e autorização
- Reuso de `auth_user` (senhas funcionam de imediato).
- Papel admin: flag/grupo Django (`is_staff` ou grupo "administradores"); o usuário
  `admin` do backup entra no grupo no saneamento. Substitui `username == 'admin'` (B10).
- Todas as mutações: `@login_required` + POST + CSRF (corrige F-13..F-23 ⚠ e F-06..F-08).
- Endpoints AJAX do admin reescritos sem `request.is_ajax()` (B1) — com htmx ou fetch.

### 3.5 O que muda vs o que não muda (resumo de paridade)
**Não muda (regra de negócio):** todo o pipeline BR-001..BR-030; textos e formatos do
rótulo; filtro ≥2024 (D-006); %VD selênio (D-006); sem recálculo retroativo ao editar
ingrediente (D-006); upload TACO com o mesmo mapeamento; chave global de cadastro;
transferência de autoria ao excluir membro.
**Muda (D-005 = corrigir):** B1 (AJAX), B2 (Biotina), B3 (Manganês 100g), B4 (fichas órfãs
— saneamento), B5, B7 (formatação robusta), B11 (filtro consistente com o corte ≥2024),
B12 (salvar item da receita recalcula), B14 (reset de senha: desabilitar UI ou configurar
e-mail — decidir), B15 (ficha sem pesos não crasha: exibe aviso), B6/B8/B9 ver nota.
**Nota B6/B8/B9:** são regras de cálculo. Corrigi-las muda números de rótulos existentes.
Proposta: corrigir apenas para **fichas novas/recalculadas** (flag por versão de cálculo),
nunca em massa — coerente com a validação de runtime (45/50 fichas divergem ao recalcular).

### 3.6 White-label por instância (D-009 — revisada)
O produto será vendido a várias empresas com **uma instância por cliente**: cada empresa
tem seu **próprio banco de dados** e, provavelmente, sua **própria hospedagem**. Um único
codebase serve todas as instâncias.

- **Sem tenant no schema**: nenhuma tabela `Organizacao`, nenhuma FK de organização,
  nenhum manager escopado — o isolamento entre empresas é físico (banco/host separados).
  O schema continua idêntico ao legado (D-003 permanece limpa).
- **Configuração por instância** (app novo `plataforma`, migration aditiva):
  modelo singleton `ConfiguracaoInstancia` com `nome_exibicao`, `logotipo`,
  `cor_primaria`, `ano_corte_ingredientes` (D-010) — editável pelo administrador da
  instância; context processor aplica o branding ao layout (D-011: o rótulo ANVISA não
  é personalizável).
- **Papéis**: grupo Django "administradores" substitui `username == 'admin'` (B10);
  sem necessidade de papéis multi-tenant.
- **Chave de cadastro** (BR-024): continua global DA INSTÂNCIA — exatamente o
  comportamento original.
- **Instância Nutri Jr**: banco restaurado do `BackupNutriJR` + saneamento
  (MIGRATION.md), com `ano_corte_ingredientes = 2024`.
- **Provisionamento de nova empresa**: criar banco vazio → `migrate` → comando
  `bootstrap_instancia` (cria config, admin inicial e chave) → deploy da instância
  (mesmo artefato, env vars próprias). Documentar runbook em docs/ quando E6 chegar.
- Fora de escopo por ora (FUTURE_IMPROVEMENTS): billing/planos, orquestração
  automatizada de provisionamento, monitoramento centralizado de instâncias.

### 3.7 UI/UX (Etapa J — depois da paridade)
Wizard com passos visíveis e validação inline; listas com paginação, busca com debounce
(htmx) e ordenação; autocomplete real no lugar do datalist por nome exato; toggles da
tabela sem reload; confirmações em modal; estados vazios e de carregamento; responsivo;
acessibilidade (labels, foco, contraste); exportação do rótulo mantendo o "Copiar para
Docs" pixel-compatível (Clipboard API com fallback).

## 4. Fases de implementação (Etapa E em diante)

1. **E1 — Fundação:** projeto config/, models compatíveis (app `fichas`, D-012),
   app `plataforma` (ConfiguracaoInstancia), `--fake-initial` sobre banco legado,
   auth + grupo administradores, base UI com branding por instância.
2. **E2 — Domínio puro:** nutrientes.py + calculo.py + rotulo.py com testes unitários
   BR-001..BR-030 e paridade attTabela.
3. **E3 — Fichas/wizard + ingredientes + upload TACO.**
4. **E4 — Rótulo final (fichaX)** validado contra o golden dataset (1.557 fichas).
5. **E5 — Membros/administração** (sem is_ajax; chave da instância; papéis por grupo).
6. **E6 — Saneamento/importação** (MIGRATION.md, incl. S7: configuração da instância
   Nutri Jr) + comando `bootstrap_instancia` para empresas novas + testes de migração.
7. **E7 — UX final, performance (selects anotados, transações), segurança.**

Critério de saída de cada fase: testes verdes + paridade golden sem regressão.
