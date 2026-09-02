# Regras de negócio

Cada regra tem um identificador `BR-XXX` citado nos comentários do código e nos testes.
Mudanças aqui alteram documentos que já foram entregues a clientes finais — trate como
decisão de produto.

## Cálculo nutricional

### BR-001 — Normalização do ingrediente para 100 g
Os nutrientes de um ingrediente são informados para `qtdeDoIngrediente` gramas (padrão
100). O sistema guarda também o valor por 100 g: `X_100g = X * 100 / qtdeDoIngrediente`.
Valor ausente conta como 0. É a base de todo o resto.

### BR-002 — Soma da receita
Para cada nutriente: `Tabela.X = Σ (ingrediente.X_100g / 100) × item.pesoLiquido`.
Usa o **peso líquido** do item, nunca o bruto.

### BR-003 — Energia por Atwater
A energia **não** é a soma da energia dos ingredientes; é recalculada:
`kcal = proteínas×4 + carboidratos×4 + gorduras totais×9` e `kJ = kcal × 4,184`.
Por isso ela pode divergir da energia declarada na fonte (TACO, rótulo do fabricante).

### BR-004 — Valores por 100 g da preparação
`X_100g = X × 100 / ficha.pesoTotal`, com o **peso total informado** pelo usuário — que
considera perdas e rendimento de cocção, e por isso difere da soma dos pesos líquidos.
Sem peso total, tudo fica zero.

### BR-005 — Valores por porção
`X_Porcao = X_100g / 100 × peso da porção`, onde o peso da porção é o **peso ANVISA**;
o peso da porção do cliente é usado só como reserva quando o ANVISA não está preenchido.

### BR-005b — Cabeçalho × colunas
O cabeçalho do rótulo (peso da porção e número de porções) é calculado na exibição, a
partir dos pesos atuais da ficha; as colunas de nutrientes vêm da tabela **gravada**.
Se os pesos mudarem sem recálculo, o rótulo declara um peso e os números correspondem a
outro. O sistema detecta essa divergência e avisa na tela do rótulo (D-017), com um botão
de recálculo explícito; `auditar_tabelas` lista os casos em toda a base.

### BR-006 — Arredondamento ANVISA
Aplicado ao valor por porção **e** ao valor por 100 g — o valor por 100 g gravado passa a
ser o arredondado, e é ele que vai ao rótulo.

- kcal e kJ: número inteiro;
- valor ≥ 10: inteiro;
- 1 ≤ valor < 10: uma casa decimal;
- valor < 1: uma casa em gramas, duas em mg/µg;
- o arredondamento é *half-down*: 32,5 → 32.

### BR-007 — Quantidades declaráveis como zero
Antes de arredondar, o valor vira 0 quando fica abaixo do limite — avaliado
separadamente por porção e por 100 g:

| Nutriente | Limite |
| --- | --- |
| Proteínas, carboidratos, fibras | ≤ 0,5 g |
| Gorduras totais | ≤ 0,5 g **e** saturadas ≤ 0,5 **e** trans ≤ 0,5 **e** monoinsaturadas = 0 **e** poli-insaturadas = 0 |
| Gorduras saturadas, gorduras trans | ≤ 0,2 g |
| Sódio | ≤ 5 mg |
| Energia | ≤ 4 kcal / ≤ 17 kJ |

Na condição por porção das gorduras totais, o valor de poli-insaturadas usado é o
**total** da receita, e não o da porção. É assimétrico em relação à condição de 100 g e
está preservado deliberadamente: mudar isso altera rótulos já emitidos.

### BR-008 — Percentual de valores diários (%VD)
`X_VD = round(100 × X_Arred / referência)`, calculado sobre o valor **já arredondado**.
As referências (dieta de 2.000 kcal) estão em `dominio/nutrientes.py`, campo
`vd_referencia`. Não têm %VD (fica 0, e a linha nunca exibe valor): potássio, retinol,
RE, RAE, piridoxina, gorduras trans, poli e monoinsaturadas.

> A referência do selênio (11) diverge da IN 75/2020, que traz 34 µg. Está mantida para
> não alterar rótulos já emitidos; corrigir é decisão de produto, e deve vir acompanhada
> de recálculo consciente das fichas afetadas.

### BR-009 — Açúcares totais e gorduras trans no %VD
Açúcares totais exibem o %VD **em branco** (não "0", nem traço), conforme a RDC 429/2020,
art. 12 §1º. Gorduras trans exibem 0 fixo.

### BR-010 — Número de porções
`numPorcoes = int(pesoPorcao / pesoAnvisa)` — quantas porções ANVISA cabem na porção do
cliente, que faz o papel de embalagem. Trunca para baixo; 0 se faltar algum peso.

## Rótulo

### BR-011 — Número de porções na exibição
Exato → "10 porções". Quebrado e maior que 3 → "Cerca de N porções". Quebrado e até 3 →
arredonda ao quarto mais próximo, em número misto: "1 e 1/2 porções", "3/4 porção".
Singular e plural corretos; ausente → "0 porções".

### BR-012 — Lupas "ALTO EM"
Por 100 g do produto (limiares de alimentos sólidos, RDC 429/2020):

| Nutriente | Limiar |
| --- | --- |
| Açúcares adicionados | ≥ 15 g |
| Gorduras saturadas | ≥ 6 g |
| Sódio | ≥ 600 mg |

As sete combinações possíveis têm imagem própria; nenhuma condição atingida → sem lupa.

### BR-013 — Formatação numérica
Inteiros sem ",0"; decimais com vírgula. Vale para as colunas de porção e de 100 g e para
o peso da porção no cabeçalho.

### BR-014 — Lista de ingredientes
Itens ordenados por peso líquido decrescente, exibidos pelo **nome fantasia**, seguidos da
composição entre parênteses quando o ingrediente tiver uma. Separados por vírgula,
terminados em ponto, com a primeira letra maiúscula.

### BR-030 — Estrutura da tabela final
Ordem e agrupamento das linhas seguem o campo `ordem_rotulo` do registro de nutrientes.
Saem indentadas: açúcares totais e adicionados, gorduras saturadas, trans, mono e
poli-insaturadas, colesterol. A linha de valor energético só aparece se kcal **e** kJ
estiverem marcados para exibição.

## Fichas e receitas

- **BR-015** — Ao criar uma ficha, cria-se a `Tabela` com o **mesmo pk**. É invariante do
  schema; várias telas contam com isso.
- **BR-016** — Só é possível adicionar itens à receita com peso total e peso da porção
  preenchidos. O ingrediente é localizado por **nome exato** (o campo tem autocompletar);
  nome não encontrado gera mensagem de erro. Cada item adicionado recalcula a tabela.
- **BR-017** — As listas de ingredientes podem esconder registros anteriores a um ano de
  corte, definido em `ConfiguracaoInstancia.ano_corte_ingredientes`. Sem configuração, não
  há corte. O filtro de busca respeita o mesmo recorte da listagem.
- **BR-018** — A receita não pode ficar sem itens: o último não é removível.
- **BR-019** — Editar um item abre tela própria; salvar grava e recalcula a tabela.
- **BR-020** — Exclusões são definitivas e em cascata: apagar uma ficha leva junto tabela,
  itens e nutrientes extras; apagar um ingrediente remove os itens de receita que o usam.
  Não há exclusão lógica.
- **BR-021** — "Finalizada" é um selo visual alternável; não bloqueia edição.

## Ingredientes

- **BR-022** — Nome de ingrediente é único; o cadastro e a edição recusam repetição.
- **BR-023** — Importação em lote: TXT separado por TAB no layout da TACO, primeira linha
  ignorada, um ingrediente por linha (`update_or_create` pelo nome). Gorduras trans são a
  soma das colunas 18:1t e 18:2t. Ao final, todos os ingredientes são renormalizados
  (BR-001).
- **Edição não retroage (D-007)** — Editar um ingrediente **não** recalcula as fichas que
  já o usam: cada ficha guarda o cálculo do momento em que foi feita, e é isso que foi
  entregue ao cliente. O recálculo é sempre explícito, ficha a ficha (D-017).

## Membros e acesso

- **BR-024** — O auto-cadastro exige a chave da instância (a mais recente cadastrada),
  senhas iguais e nome de usuário livre. Cria `User` + `Membro` ligados.
- **BR-025** — O administrador (membro do grupo `administradores`) vê a chave atual e pode
  trocá-la, redefinir a senha de qualquer membro e excluir membros.
- **BR-026** — Excluir um membro exige escolher um destino diferente: fichas e ingredientes
  têm a autoria transferida **antes** da exclusão, e a mensagem informa quantos itens
  foram transferidos.
- **BR-027** — Abrir a tela de login (ou de cadastro) encerra a sessão atual.

## Listagens

- **BR-028** — Fichas e ingredientes filtram por trecho do texto (E lógico entre os
  campos); fichas ordenadas da mais recente para a mais antiga. Filtros viajam na URL
  (GET) e as listas são paginadas de 25 em 25.
- **BR-029** — Na tela da tabela nutricional, os valores brutos, por 100 g e por porção são
  exibidos truncados, para caber sem distorcer o número.
