# UI do Sistema Original — Nutri Jr

## Layout base (`base_layout.html`)
- Header fixo com logo/ícone e navbar: **Fichas** (listaFichas), **Ingredientes**
  (listaIngredientes), **Membros** (listaMembros), **Ajuda**, **Sair** (logout).
- Bloco de mensagens flash (sucesso/erro) no topo do conteúdo.
- Bootstrap 3.3.7 **e** 4.3.1 + Font Awesome 4.7 via CDN; CSS próprio por tela em
  `assets/fichas/`. Sem dark mode, sem responsividade planejada (larguras fixas em px/%).
- Sem paginação em nenhuma lista; sem ordenação clicável; sem estados de loading;
  estado vazio = tabela sem linhas.

## Telas (13)

### 1. Login (`login.html`, pública)
Campos Nome/Senha; mensagens de erro via flash; link para cadastro ("Registre-se").
Ao entrar: redireciona para Lista de Fichas.

### 2. Cadastro de membro (`registrarMembro.html`, pública)
Nome, Semestre de entrada, E-mail, Senha, Confirmar senha, Chave. Erros: nome já existente,
senhas diferentes, chave incorreta. Sucesso → volta ao fluxo logado (listaFichas — mas o
usuário NÃO é logado automaticamente [CONFIRMADO: view não chama login()]).

### 3. Lista de fichas (`fichas_registradas.html`)
Filtros (Receita, Cliente, Autor — POST, contains) + botão "Nova ficha".
Tabela: nome, cliente, autor, data, selo Finalizada; clique leva à fichaX.

### 4. Ficha passo 1 — dados base (`registrarFichaBase.html`)
Form: Autor (select ordenado por nome), Cliente, Nome da receita, Peso total (g),
Peso da porção Cliente (g), Peso da porção Anvisa, Medida caseira da porção,
Data de criação (DD/MM/YYYY). Botões Salvar (→ passo 2) e Cancelar (→ lista).
Mostra "Logado agora: <username>" ao lado do campo Autor.

### 5. Ficha passo 2 — receita (`receita.html`)
- Card "Dados Gerais" com resumo da ficha.
- Tabela dos itens: Ingrediente (link p/ editar ingrediente em nova aba), Nome Fantasia,
  Peso Bruto, Peso Líquido, Medida Caseira, Editar (lápis), X (remover — só se >1 item).
- Form de adição: input com **datalist** (autocomplete dos ingredientes ≥2024) + campos do item.
- Pré-visualização da tabela nutricional parcial.
- Navegação do wizard (passos 1/2/3) + link para fichaX.

### 6. Editar item da receita (`editarReceita.html`)
Form isolado com os 4 campos do item; salvar → volta ao passo 2.

### 7. Ficha passo 3 — tabela nutricional (`tabelaNutricional.html`)
- Tabela completa dos 46 nutrientes: valor total, por 100 g, por porção (truncados a 5 casas),
  arredondado, %VD, unidade e **toggle de visibilidade** (ícone olho/link `atualizarMostrar`).
- Form para nutriente extra manual (nome, qtde real, qtde arredondada, medida, %VD).
- Lista dos nutrientes extras com excluir.
- Textarea "Informações Complementares" (ex.: "Não contém quantidades significativas de …").
- Submit → salva informações e vai para fichaX.

### 8. Visualização final (`fichax.html`)
- Cabeçalho: nome, autor, data, cliente, pesos, nº de porções (formato ANVISA), selo FINALIZADA.
- Botão "Marcar como finalizada" (toggle) e **"Copiar tudo"** (seleciona o bloco e
  `document.execCommand('copy')` com ajuste de tamanho das imagens para o Google Docs).
- **Modelo de tabela vertical** e **modelo linear** do rótulo: "Porções por embalagem",
  "Porção: Xg (medida caseira)", colunas 100 g / porção / %VD, seções com linhas tracejadas,
  itens indentados, rodapé "*Percentual de valores diários…".
- Lista de ingredientes ordenada por peso (nomes fantasia + composição).
- Lupa(s) ANVISA "ALTO EM" (imagem base64) quando aplicável.
- Informações complementares.
- Navegação: Lista de Fichas, Editar Base (1/3), Editar Receita (2/3), Editar Final (3/3),
  Deletar ficha (confirm JS).

### 9. Lista de ingredientes (`ingredientes_registrados.html`)
Filtros (Nome, Origem, Autor) + botão registrar + botão upload. Tabela com nome, origem,
autor, data; ações editar/excluir (excluir com confirm). Mostra só ingredientes ≥2024
(até filtrar — o filtro busca em tudo).

### 10. Registrar/editar ingrediente (`registrarIngrediente.html`)
Autor, Ingrediente, Composição, Fonte/Marca, Quantidade do ingrediente (g), nº ref.,
data, e os 46 campos de nutrientes em grade (labels vazios, organizados por colunas
com cabeçalhos no template).

### 11. Upload (`upload.html`)
Input de arquivo TXT (TAB, padrão TACO) + instruções; erros via flash.

### 12. Membros (`usuarios_registrados.html`)
Tabela: nome, semestre, e-mail. Se admin: exibe a chave atual e 3 painéis AJAX (jQuery):
trocar chave, trocar senha de membro, excluir membro com transferência de autoria
(feedback em `#mensagens`, alert JS no delete).

### 13. Ajuda (`ajuda.html`)
Texto estático com instruções de uso.

## Decisões de UI vs regras de negócio
Coisas que são só UI (podem mudar na nova versão): Bootstrap duplicado, tabelas sem paginação,
filtros via POST, confirmações via `confirm()`, cópia via execCommand (deprecated),
datalist para escolher ingrediente por nome exato.
Coisas que parecem UI mas são regra: formato exato do rótulo (vertical/linear, indentação,
traços), textos das mensagens de erro/sucesso, formato de porções, vírgula decimal,
lupas e sua posição — tudo isso é saída "oficial" copiada para documentos de clientes.
