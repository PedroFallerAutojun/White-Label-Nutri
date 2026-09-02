# Banco de dados

PostgreSQL. Um banco por empresa cliente — não há coluna nem tabela de organização.
As tabelas do domínio ficam sob o prefixo `fichas_`; o app `plataforma` acrescenta a
configuração da instância. Autenticação usa as tabelas padrão do Django (`auth_user`,
`auth_group`…).

## Modelo lógico

```
auth_user 1──1 fichas_membro
                    │ 1                        │ 1
                    ▼ N                        ▼ N
            fichas_ingrediente          fichas_ficha ──1──1── fichas_tabela ──1──N── fichas_nutriente
                    │ N                        │ 1
                    └──────► fichas_ficha_ingrediente ◄──────┘
                             (item da receita, com pesos e medida caseira)

fichas_chave                     — chave de auto-cadastro da instância
plataforma_configuracaoinstancia — branding e regras da instância (uma linha)
```

## Tabelas

**fichas_membro** — perfil do usuário. Relação 1–1 com `auth_user` (exclusão em cascata).
Campos: nome, semestre, e-mail. É o autor de fichas e ingredientes.

**fichas_ingrediente** — composição nutricional de um insumo para `qtdeDoIngrediente`
gramas. Além dos campos de identificação (nome, composição, fonte/marca, nº de referência,
data), traz **46 pares `nutriente` / `nutriente_100g`** em ponto flutuante. O par existe
porque o usuário informa os valores na quantidade que tiver em mãos (uma lata de 395 g,
por exemplo) e o sistema guarda também a versão normalizada por 100 g (BR-001).

**fichas_ficha** — cabeçalho da ficha técnica: cliente, nome da receita, data, selo
"finalizada" e os pesos: `pesoTotal` (informado, base do cálculo por 100 g),
`pesoPorcao` (porção do cliente / embalagem), `pesoAnvisa` (porção ANVISA),
`pesoLiquidoPreparacao` (soma dos itens, calculada), `numPorcoes` e a medida caseira.

**fichas_ficha_ingrediente** — item da receita: ficha, ingrediente, peso bruto, peso
líquido (base de todo o cálculo), medida caseira e nome fantasia (o nome que aparece no
rótulo).

**fichas_tabela** — a tabela nutricional calculada e **persistida** de uma ficha. Para
cada um dos 46 nutrientes guarda `X` (total), `X_100g`, `X_Porcao`, `X_Arred`, `X_VD`,
`X_Mostrar` (vai ao rótulo?) e `X_unidadeMd` (unidade exibida), além das informações
complementares. Vêm marcados por padrão os obrigatórios da ANVISA: energia (kcal e kJ),
carboidratos, açúcares totais e adicionados, proteínas, gorduras totais, saturadas e
trans, fibras e sódio.

**fichas_nutriente** — linha extra manual no rótulo, para itens que não vêm dos
ingredientes cadastrados. Pertence a uma tabela.

**fichas_chave** — chave de auto-cadastro. A aplicação sempre usa a **última** linha;
trocar a chave insere uma nova, preservando o histórico.

**plataforma_configuracaoinstancia** — uma única linha, com a identidade da instância:
nome de exibição, cor primária, ano de corte de ingredientes e o **logotipo guardado no
próprio banco** (conteúdo binário, tipo do arquivo e data de atualização). O logotipo fica
no banco porque as plataformas de deploy usam disco efêmero — um arquivo enviado pelo
cliente sumiria no próximo restart (D-020). Ele é enviado pelo Django admin e servido em
`/branding/logotipo`.

## Invariantes e pontos de atenção

- **`Tabela.pk == Ficha.pk`** (BR-015). Não é só uma chave estrangeira: várias telas
  buscam a tabela pelo id da ficha. `servicos.obter_tabela()` cria a tabela se faltar.
- **As chaves primárias são `AutoField`** (inteiro), não `BigAutoField` — definido em
  `DEFAULT_AUTO_FIELD`. Mudar isso quebra a compatibilidade com bases existentes.
- **O label do app é `fichas`**: é ele que dá nome às tabelas e identifica as migrations
  registradas no banco. Não renomear em bases já em uso.
- **Tudo em ponto flutuante.** Os valores acumulam ruído (aparecem números como
  1.0000000000000002); comparações em testes usam tolerância.
- **A tabela é um cache materializado**, não uma view: ela guarda o cálculo do momento em
  que a ficha foi editada, que é o que foi entregue ao cliente. Nada recalcula em massa
  (D-007); `auditar_tabelas` mostra o que está defasado.
- **Modelo largo por natureza**: 46 nutrientes × 7 colunas na tabela e × 2 no ingrediente.
  É consequência de o rótulo ser um documento fixo. Se um dia for normalizado
  (`nutriente(chave, valor)`), a migração precisa de conferência rótulo a rótulo.

## Cópias de segurança

Cada instância é responsável pelo próprio backup — em geral o snapshot automático do
provedor de banco. Um `pg_dump` guarda dados de cliente: trate a cópia como material
confidencial e nunca a versione no repositório (o `.gitignore` já barra `*.sql` e
`*.dump`).
