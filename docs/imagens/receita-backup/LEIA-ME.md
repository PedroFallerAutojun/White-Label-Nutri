# Prints — receita montada com ingredientes do BackupNutriJR

O arquivo `BackupNutriJR` não está (e não deve estar) no repositório — `backups/`
é ignorado pelo git e o dump é dado de cliente. O que existe versionado são os
**goldens de paridade** (`tests/golden/golden_paridade.json.gz`), que guardam, para
cada uma das 1558 fichas do backup, os pesos da ficha, os itens da receita e os
valores `X_100g` reais de cada ingrediente usado.

Estas capturas reproduzem a **ficha 5 do backup** numa instância limpa: os dez
ingredientes foram criados a partir dos valores do golden e a receita foi montada
pela interface, com os pesos e as medidas caseiras originais
(peso total 1230 g, porção de 5 g, "NÃO CONTÉM GLÚTEN. ALÉRGICOS: CONTÉM SOJA.").

Conferência do resultado contra o golden (46 nutrientes × total, `_100g`, `_Porcao`,
`_Arred` e `_VD` = 230 comparações): **nenhuma divergência**, e
`pesoLiquidoPreparacao` = 1276 g e `numPorcoes` = 0 iguais aos do sistema original.
O rótulo ainda dispara a lupa **ALTO EM SÓDIO** (BR-012), com 1324 mg/100 g.

| Print | Tela | O que mostra |
| --- | --- | --- |
| `01-ingredientes-do-backup.png` | `/listaIngredientes?f_origemDosDados=BackupNutriJR` | Os dez ingredientes importados do acervo. |
| `02-passo1-pesos-do-backup.png` | `/registrarFicha1` | Passo 1/3 com os pesos originais da ficha 5. |
| `03-passo2-primeiro-item.png` | `/registrarFicha2/<pk>` | Primeiro item (sal, 5 g, colher de chá) sendo adicionado. |
| `04-passo2-receita-do-backup.png` | `/registrarFicha2/<pk>` | Os dez itens da receita original. |
| `05-passo3-tabela-calculada.png` | `/registrarFicha3/<pk>` | Tabela recalculada pelo sistema novo. |
| `06-passo3-complementares-do-backup.png` | `/registrarFicha3/<pk>` | Açúcares adicionados fora do rótulo e os alérgicos originais. |
| `07-rotulo-final.png` | `/fichaX/<pk>` | Rótulo final com a lupa ALTO EM SÓDIO. |

Para reproduzir com o acervo completo (e não só com o golden), coloque uma cópia do
`BackupNutriJR` em `backups/` e siga `backups/LEIA-ME.md`.
