# Testes

```bash
pytest -q                       # suíte completa
pytest tests/unit -q            # só o domínio (rápido, sem banco)
pytest -q -k rotulo             # por nome
```

O pytest-django cria e destrói o banco de teste a partir da `DATABASE_URL`, então basta
ter um PostgreSQL acessível. A configuração está em `pytest.ini`.

## O que cada camada cobre

**`tests/unit/` — domínio puro (23 testes).**
Arredondamento ANVISA e *half-down* com os casos de borda (BR-006), limites de declaração
de zero (BR-007), integridade do registro de nutrientes: unidades válidas, ordem do rótulo
sem buracos, referências de %VD e quais linhas saem indentadas (BR-008/BR-030).

**`tests/integration/test_fichas.py` (39 testes).**
O wizard inteiro com asserções no banco depois de cada passo: criação da ficha com a
tabela de mesmo pk (BR-015), soma da receita e energia por Atwater (BR-002/BR-003),
valores por 100 g e por porção (BR-004/BR-005), %VD (BR-008), montagem do rótulo nos dois
modelos, lupas (BR-012), lista de ingredientes por peso (BR-014), guardas de receita
(BR-016/BR-018), corte de ingredientes por ano (BR-017) e o aviso de tabela desatualizada
(BR-005b/D-017).

**`tests/integration/test_membros.py` (20 testes).**
Cadastro com chave (BR-024), papel de administrador (BR-025), troca de chave e de senha,
exclusão com transferência de autoria (BR-026) e o logout ao abrir o login (BR-027).

**`tests/integration/test_seguranca.py` (16 testes).**
Rotas protegidas exigem autenticação; mutações exigem POST e token CSRF; senha fraca é
recusada; o fluxo de reset por e-mail não está exposto; e as garantias de
`config.settings.prod` (HTTPS, cookies, HSTS, `X-Frame-Options`, obrigatoriedade de
`SECRET_KEY` e `ALLOWED_HOSTS`).

**`tests/integration/test_fundacao.py` (7 testes).**
Models, migrations sem pendências, configuração da instância e branding no layout.

**`tests/integration/test_comandos.py` (4 testes).**
`bootstrap_instancia`: provisionamento completo, recusa de instância já configurada e de
usuário existente, e o cenário de venda ponta a ponta — provisionar, cadastrar um membro
com a chave e entrar no sistema.

## Ao mexer no cálculo ou no rótulo

Os valores gravados nas fichas são os rótulos entregues aos clientes. Antes de alterar
`dominio/calculo.py`, `dominio/arredondamento.py` ou `dominio/rotulo.py`:

1. leia a regra correspondente em [REGRAS_DE_NEGOCIO.md](REGRAS_DE_NEGOCIO.md);
2. escreva o teste do comportamento novo **antes** da mudança;
3. rode `python manage.py auditar_tabelas` numa cópia da base de um cliente para
   dimensionar quantas fichas mudariam de resultado;
4. lembre que fichas existentes não são recalculadas automaticamente (D-007) — a mudança
   só aparece nas fichas novas e nas recalculadas à mão.

## Integração contínua

`.github/workflows/testes.yml` roda a cada push: sobe um PostgreSQL, instala as
dependências, executa `manage.py check`, verifica que não há migrations pendentes
(`makemigrations --check`) e roda a suíte.
