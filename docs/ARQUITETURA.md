# Arquitetura

## Stack

| Camada | Escolha |
| --- | --- |
| Linguagem | Python 3.12+ |
| Framework | Django 5.2 LTS |
| Banco | PostgreSQL 14+ |
| Front-end | Django Templates + Bootstrap 5 (servido pela própria aplicação) |
| Configuração | django-environ (12-factor: tudo por variável de ambiente) |
| Estáticos | WhiteNoise |
| Servidor | gunicorn (`Procfile`) |
| Testes | pytest + pytest-django |

Sem SPA, sem jQuery, sem CDN. As páginas são renderizadas no servidor; o JavaScript
próprio se resume à cópia do rótulo para a área de transferência.

## Estrutura

```
White-Label-Nutri/
├── config/                  # settings (base/dev/prod), urls, wsgi
├── apps/
│   ├── plataforma/          # ConfiguracaoInstancia (branding) e comandos de gestão
│   └── fichas/              # domínio do produto
│       ├── models.py        #   Membro, Ingrediente, Ficha, Tabela, Ficha_Ingrediente…
│       ├── views.py         #   todas as telas
│       ├── forms.py         #   formulários e validações
│       ├── servicos.py      #   ponte models ↔ domínio (recálculo, conferência)
│       └── dominio/         #   NÚCLEO PURO, sem Django:
│           ├── nutrientes.py    #     registro dos 46 nutrientes
│           ├── calculo.py       #     BR-001..BR-010
│           ├── arredondamento.py#     BR-006/BR-007
│           ├── rotulo.py        #     BR-009..BR-014, BR-030
│           └── lupas_img.py     #     imagens das lupas "ALTO EM"
├── templates/ · static/
├── tests/{unit,integration}/
└── docs/
```

### O núcleo de domínio é puro

`apps/fichas/dominio/` não importa Django. Recebe números, devolve números. Isso torna
todo o cálculo nutricional testável sem banco e impede que uma mudança de tela altere um
rótulo por acidente. Quem faz a ponte é `servicos.py`: lê a ficha e a receita, chama
`calculo.calcular()` e grava o resultado na `Tabela` em uma única transação.

### Registro único de nutrientes

Os 46 nutrientes são declarados **uma vez**, em `dominio/nutrientes.py`, como uma tupla de
`NutrienteDef` com chave, unidade, referência de %VD, limite para declarar zero, se aparece
por padrão no rótulo, texto e posição no rótulo. Models, cálculo, formulários e templates
iteram sobre esse registro em vez de repetir 46 blocos.

Adicionar ou alterar um nutriente é editar esse arquivo — e, se houver coluna nova,
gerar a migration correspondente.

## Configuração e ambientes

`config/settings/base.py` traz o comum; `dev.py` liga o DEBUG; `prod.py` exige
`SECRET_KEY` e `ALLOWED_HOSTS` (a aplicação **não sobe** sem elas) e aplica as garantias
de segurança. Tudo o que varia entre instâncias vem de variável de ambiente ou da
`ConfiguracaoInstancia` — ver [OPERACAO.md](OPERACAO.md).

## Segurança

- Toda mutação exige login (`@login_required`), método POST e token CSRF.
- Registro inexistente devolve 404, nunca 500 (`get_object_or_404`).
- Papel administrativo por **grupo do Django** (`GRUPO_ADMINISTRADORES`), não por nome de
  usuário.
- Senhas passam pelos validadores do Django, com mínimo de 10 caracteres.
- Em produção: HTTPS forçado, cookies `Secure`/`HttpOnly`/`SameSite=Lax`, HSTS de 1 h por
  padrão, `X-Frame-Options: DENY`, `nosniff`, sessão expirando em 12 h de inatividade e
  upload limitado a 5 MB.
- `HSTS includeSubDomains`/`preload` ficam **desligados** por padrão: o efeito é difícil de
  reverter e afeta todos os subdomínios do cliente. Habilite por variável de ambiente
  quando tiver certeza de que todo o domínio serve HTTPS.
- As URLs de recuperação de senha por e-mail **não são expostas**: não há backend de
  e-mail configurado, e um fluxo de reset quebrado é pior que a ausência dele. A tela de
  login orienta a procurar um administrador, que redefine a senha na tela de Membros.

## Decisões registradas

Decisões que o código cita pelo identificador. Mudá-las é decisão de produto, não de
implementação.

| ID | Decisão |
| --- | --- |
| D-007 | Os valores gravados na `Tabela` são a fonte de verdade histórica: representam os rótulos já emitidos aos clientes. Nada recalcula tabelas em massa. |
| D-009 | Uma instância por empresa: banco e hospedagem próprios, sem tenant no schema. |
| D-010 | O corte de ingredientes por ano é configuração da instância (`ano_corte_ingredientes`), não regra fixa. |
| D-011 | A personalização white-label se limita à interface. O rótulo ANVISA é igual para todas as empresas. |
| D-013 | Garantias de segurança de produção (lista acima), com HSTS conservador por padrão. |
| D-014 | Reset de senha por e-mail não exposto; redefinição é feita por um administrador. |
| D-015 | Listagens paginadas (25 por página) com filtros por GET, para que a busca seja compartilhável por link. |
| D-016 | Bootstrap servido pela aplicação (`static/vendor/`), sem CDN: funciona offline e não expõe requisições dos clientes a terceiros. |
| D-017 | Tabela desatualizada é **detectada e avisada**, nunca recalculada em silêncio: a tela do rótulo compara o gravado com o cálculo atual e oferece um botão de recálculo explícito, ficha a ficha. |
| D-018 | Número de porções = peso da porção do cliente ÷ peso da porção ANVISA (quantas porções ANVISA cabem na embalagem). |
