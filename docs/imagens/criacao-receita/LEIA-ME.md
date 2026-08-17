# Prints — criação de uma nova receita (ficha técnica)

Capturas do fluxo FL-01 (`docs/FLOWS.md`), feitas em uma instância limpa
("Nutri Demo") com cinco ingredientes de exemplo da TACO. Receita usada:
*Bolo de cenoura caseiro*, 1000 g de preparação, porção de 80 g.

| Print | Tela | O que mostra |
| --- | --- | --- |
| `01-login.png` | `/loginUser` | Entrada no sistema. |
| `02-lista-fichas.png` | `/listaFichas` | Ponto de partida, antes de existir a ficha. |
| `03-passo1-dados-base.png` | `/registrarFicha1` | Passo 1/3: autor, cliente, nome, pesos e medida caseira. |
| `04-passo2-receita-vazia.png` | `/registrarFicha2/<pk>` | Passo 2/3 logo após criar a ficha (BR-015: ficha + tabela). |
| `05-passo2-adicionando-ingrediente.png` | `/registrarFicha2/<pk>` | Formulário preenchido com o primeiro ingrediente (datalist + pesos). |
| `06-passo2-receita-completa.png` | `/registrarFicha2/<pk>` | Cinco itens na receita e os totais já recalculados (attTabela). |
| `07-passo3-tabela-nutricional.png` | `/registrarFicha3/<pk>` | Passo 3/3: valores por 100 g, por porção, arredondado e %VD. |
| `08-passo3-rotulo-e-complementares.png` | `/registrarFicha3/<pk>` | Cálcio e Ferro marcados para o rótulo + informações complementares. |
| `09-ficha-final-rotulo.png` | `/fichaX/<pk>` | Rótulo ANVISA final nos modelos vertical e linear. |
| `10-lista-fichas-com-a-nova.png` | `/listaFichas` | A ficha recém-criada na listagem. |
