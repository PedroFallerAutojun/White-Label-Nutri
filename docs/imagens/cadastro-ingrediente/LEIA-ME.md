# Prints — cadastro de ingrediente

Capturas feitas na mesma instância de demonstração das prints de criação de receita
(`docs/imagens/criacao-receita/`). Ingrediente cadastrado: *Leite condensado integral
(lata 395 g)*, com os nutrientes informados para os 395 g da lata — o sistema
normaliza tudo para 100 g (BR-001), o que aparece na coluna `kcal/100g` da listagem
(1236 kcal na lata → 312,9 kcal/100 g).

| Print | Tela | O que mostra |
| --- | --- | --- |
| `01-lista-ingredientes.png` | `/listaIngredientes` | Listagem com filtros por nome, fonte e autor. |
| `02-novo-ingrediente-em-branco.png` | `/registrarIngrediente` | Formulário vazio: identificação + os 46 campos de nutrientes. |
| `03-identificacao-preenchida.png` | `/registrarIngrediente` | Bloco de identificação: nome, autor, composição, fonte, quantidade de referência e data. |
| `04-composicao-nutricional.png` | `/registrarIngrediente` | Bloco de composição, com os valores da lata inteira. |
| `05-formulario-completo.png` | `/registrarIngrediente` | Formulário inteiro pronto para salvar. |
| `06-ingrediente-cadastrado.png` | `/listaIngredientes` | Confirmação e o ingrediente já normalizado por 100 g. |
| `07-busca-do-ingrediente.png` | `/listaIngredientes?f_nomeIng=…` | Filtro por nome localizando o registro novo. |
| `08-nome-duplicado-recusado.png` | `/registrarIngrediente` | Nome repetido é recusado com mensagem de erro. |
| `09-upload-em-lote-taco.png` | `/upload` | Alternativa ao cadastro manual: importação em lote do TXT da TACO (BR-023). |
