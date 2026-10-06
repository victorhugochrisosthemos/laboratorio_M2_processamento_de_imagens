# Relatório — Laboratório M2.1

## Alvo e imagens

O alvo escolhido foi o conjunto de traços escuros que formam caracteres e símbolos em páginas. A ideia é produzir uma máscara em que tinta ou traço apareça como `255` e o fundo como `0`. Esse alvo também é útil para o M2.2, porque caracteres, símbolos e fragmentos de traço geram componentes que podem ser analisados e contados posteriormente.

Foram usadas duas imagens. `printed_page.png` contém texto impresso com contraste relativamente alto, apesar de existir um gradiente de iluminação. `handwritten_notes.png` é o caso mais difícil: os símbolos estão sobre linhas do caderno, há perspectiva e o contraste entre escrita e papel varia bastante.

Os arquivos de entrada foram mantidos sem edição. A origem e os hashes estão em `IMAGE_SOURCES.md`.

## Configurações comparadas

As duas configurações começam com conversão para cinza e filtro Gaussiano `3x3`. O filtro foi mantido pequeno para reduzir variações locais e ruído sem apagar demais os traços finos.

Na primeira configuração foi usado limiar fixo `T = 115`. Como o alvo é mais escuro que o fundo, a saída foi invertida (`THRESH_BINARY_INV`). Na segunda foi usado limiar adaptativo Gaussiano, também invertido, com janela `31x31` e `C = 8`.

| Configuração | Pré-processamento | Parâmetros principais |
|---|---|---|
| Fixo | Gaussiano `3x3` | `threshold=115`, invertido |
| Adaptativo | Gaussiano `3x3` | `block-size=31`, `C=8`, invertido |

## Resultado quantitativo

A tabela abaixo mostra a proporção de pixels classificados como primeiro plano. Não existe máscara de referência para essas imagens, portanto esse número não é tratado como acurácia, precisão ou revocação; ele serve apenas para comparar quanto de cada imagem foi marcado.

| Imagem | Fixo | Adaptativo |
|---|---:|---:|
| `printed_page.png` | 17,55% | 17,39% |
| `handwritten_notes.png` | 18,08% | 14,07% |

As máscaras finais têm a mesma largura e altura da entrada, um único canal e somente os valores `{0, 255}`. Essa verificação também é feita automaticamente pelo programa.

## Comparação visual

### Página impressa

![Comparação da página impressa](images/output/printed_page_comparison.png)

No limiar fixo, a região mais escura do lado esquerdo tende a virar primeiro plano junto com os caracteres, enquanto partes mais claras do texto perdem pixels. O adaptativo acompanha melhor a mudança de iluminação ao longo da página e mantém os caracteres de forma mais uniforme. A sobreposição ainda mostra pequenos trechos de fundo marcados, principalmente em linhas e bordas de contraste.

### Anotações manuscritas

![Comparação das anotações](images/output/handwritten_notes_comparison.png)

Neste caso o problema principal não é apenas iluminação. As linhas do caderno têm intensidade parecida com vários traços manuscritos e aparecem como falsos positivos nos dois métodos. O limiar fixo também engrossa regiões escuras e junta detalhes próximos. O adaptativo reduz parte desse excesso, mas não consegue separar semanticamente “linha do papel” de “escrita”, porque ambos são traços escuros locais.

## Escolha para o M2.2

A configuração adaptativa foi escolhida como máscara de trabalho. Na página impressa ela é visualmente mais estável diante do gradiente de iluminação. Na imagem manuscrita ela reduz a área total marcada de 18,08% para 14,07% e evita parte das regiões largas produzidas pelo limiar fixo. Ainda permanecem falsos positivos causados pelas linhas do caderno e pequenos falsos negativos em traços muito claros.

Os arquivos escolhidos para continuidade são `printed_page_mask.png` e `handwritten_notes_mask.png`, ambos cópias das máscaras obtidas pelo método adaptativo.

## Respostas pedidas

**(a) Em que casos o limiar fixo funcionou ou falhou?** Ele funciona melhor nas partes da página impressa em que texto e fundo mantêm contraste parecido. Falha quando a intensidade do fundo muda ao longo da imagem e, na imagem manuscrita, quando linhas do caderno e escrita ocupam faixas de cinza próximas. Nesses pontos aparecem tanto regiões de fundo marcadas quanto trechos de escrita incompletos.

**(b) Qual parâmetro foi mais sensível?** O valor de `threshold` do método fixo foi o parâmetro mais sensível nos testes. Na imagem manuscrita, mantendo o filtro `3x3`, a proporção de primeiro plano sobe de 14,05% em `T=110` para 18,08% em `T=115`, 23,02% em `T=120` e 39,66% em `T=130`. Uma variação pequena no limiar muda bastante a quantidade de fundo incorporada à máscara.

**(c) Quais erros podem atrapalhar a contagem no M2.2?** Linhas do caderno podem ser contadas como componentes que não pertencem ao alvo. Traços de uma mesma letra podem se desconectar e virar vários componentes, enquanto letras próximas podem se unir e virar um único componente. Pequenos buracos ou falhas nos caracteres também alteram a topologia da máscara. Por isso, uma contagem direta de componentes conectados exigirá filtragem por área, forma ou operações morfológicas antes de ser interpretada como quantidade de caracteres.
