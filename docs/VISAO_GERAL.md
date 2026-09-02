# Visão geral

O White-Label-Nutri é um sistema web para **fichas técnicas de preparações e tabelas
nutricionais no padrão ANVISA**. Quem usa é uma equipe de nutrição que precisa entregar
ao cliente final um rótulo pronto para impressão, calculado a partir da receita.

## O que o sistema faz

1. **Cadastro de ingredientes** — composição nutricional de cada insumo (46 nutrientes),
   informada para uma quantidade de referência e normalizada para 100 g. Pode ser feito
   um a um ou em lote, importando o TXT da tabela TACO.
2. **Ficha técnica em três passos** — dados da preparação e pesos → receita (ingredientes,
   pesos bruto e líquido, medida caseira) → escolha do que aparece no rótulo.
3. **Rótulo ANVISA** — tabela nutricional nos modelos vertical e linear, com %VD, lista
   de ingredientes em ordem de peso, alérgicos e as lupas "ALTO EM" quando aplicável.
   Um botão copia o bloco pronto para colar no Google Docs.
4. **Membros e administração** — cadastro por chave da instância, papel de administrador
   para trocar a chave, redefinir senhas e remover membros transferindo a autoria.

## Modelo de entrega: uma instância por empresa

Cada empresa cliente roda o **seu próprio deploy**, com banco de dados e hospedagem
próprios. O código é o mesmo para todas; o que muda é a configuração.

- **Não existe conceito de "organização" dentro do banco** — nenhuma tabela de tenant,
  nenhuma coluna de empresa, nenhum filtro por cliente. O isolamento é físico: bancos
  separados. Isso mantém o schema simples e elimina a classe inteira de bugs de
  vazamento de dados entre clientes.
- **A personalização é de interface**: nome de exibição, logotipo e cor primária, no
  modelo `ConfiguracaoInstancia` (app `plataforma`), editável pelo Django admin.
- **O rótulo não é personalizável.** Formato, ordem, arredondamento e textos seguem a
  regulamentação (RDC 429/2020 e IN 75/2020) e são iguais em todas as instâncias.
- Provisionar uma empresa nova é: criar banco → `migrate` → `bootstrap_instancia` →
  deploy. Ver [OPERACAO.md](OPERACAO.md).

## Documentação

| Documento | Conteúdo |
| --- | --- |
| [ARQUITETURA.md](ARQUITETURA.md) | Stack, estrutura do código, camada de domínio, segurança |
| [REGRAS_DE_NEGOCIO.md](REGRAS_DE_NEGOCIO.md) | BR-001..BR-030: cálculo, rótulo, fichas, ingredientes, membros |
| [BANCO_DE_DADOS.md](BANCO_DE_DADOS.md) | Modelo de dados, invariantes e pontos de atenção |
| [INTERFACE.md](INTERFACE.md) | As telas, com capturas |
| [OPERACAO.md](OPERACAO.md) | Provisionar, publicar, configurar e manter uma instância |
| [TESTES.md](TESTES.md) | Como rodar a suíte e o que cada camada cobre |
