# Relatório técnico — M2.1 e M2.2

**Aluno:** Victor Hugo Chrisosthemos Teixeira  
**Disciplina:** Processamento de Imagens — 2026/02

## M2.1 — Máscara binária e segmentação

### Objetivo e entradas

O objetivo foi separar oito discos escuros de um fundo mais claro. Preparei duas imagens sintéticas de 360 × 240 pixels com os mesmos discos, mas iluminação diferente: `scene_uniform.png`, com fundo aproximadamente uniforme, e `scene_uneven.png`, com um gradiente de luminosidade. Os dados foram gerados de forma reproduzível pelo arquivo `tools/generate_inputs.py`. As máscaras de referência estão em `images/reference/`.

Em ambas as imagens, o branco da máscara significa objeto e o preto significa fundo. A máscara fica com o tamanho da entrada, um canal e somente os valores 0 e 255.

### Métodos, parâmetros e comparação

- **Fixo:** limiar global 120, usando `THRESH_BINARY_INV`. Pixels com intensidade menor ou igual a 120 são classificados como objeto. É uma configuração simples, mas pode incluir fundo escuro quando a iluminação é desigual.
- **Adaptativo gaussiano:** tamanho de bloco 75, `C=8` e `THRESH_BINARY_INV`. O limiar varia conforme a vizinhança; isso lida melhor com o gradiente, mas pode perder detalhes internos dos discos.
- **Pré-processamento:** não há filtro de suavização antes da segmentação. Assim fica mais simples atribuir as diferenças de resultado à escolha do limiar. O método de Otsu é disponibilizado na CLI como alternativa extra.

As quantidades abaixo são contagens obtidas na execução com Python 3.13.5, OpenCV 4.13.0 e NumPy 2.3.5. A comparação de erros é possível porque a cena foi desenhada com uma referência binária conhecida.

| Cena | Método | Pixels de fundo incluídos por erro | Pixels de objeto perdidos | Total de pixels classificados errado |
|---|---|---:|---:|---:|
| Uniforme | Fixo 120 | 20 | 87 | 107 |
| Uniforme | Adaptativo 75 / C=8 | 24 | 350 | 374 |
| Desigual | Fixo 120 | 8.922 | 87 | 9.009 |
| Desigual | Adaptativo 75 / C=8 | 31 | 1.085 | 1.116 |

Em iluminação uniforme, o limiar fixo teve menos erros. Quando o fundo escurece de um lado, o mesmo limiar confunde parte do fundo com os discos. A alternativa adaptativa reduz muito essa inclusão indevida, apesar de aumentar os pixels perdidos. Por isso escolhi a **máscara adaptativa para continuar os dois cenários no M2.2**, mantendo o mesmo método de ponta a ponta. Isso não significa que ele sempre supera o limiar fixo.

Para conferir visualmente, abra `images/output/scene_uniform_errors.png` e `images/output/scene_uneven_errors.png`. Nelas, esquerda = fixo e direita = adaptativo; vermelho = fundo incluído, azul = pedaço de disco excluído. Os arquivos `scene_*_fixed.png` e `scene_*_adaptive.png` guardam as máscaras usadas na comparação. Os JSON ao lado registram os parâmetros e a proporção de pixels brancos. Essa proporção indica a quantidade segmentada, **não** a qualidade por si só.

### Limitações observadas

O limiar fixo depende fortemente da claridade do fundo. Já a versão adaptativa pode perder partes do disco, especialmente quando a janela local é influenciada pelo próprio objeto. Nas duas versões, as marcas claras dentro de alguns discos também geram buracos. Os pequenos pontos escuros sobre o fundo podem virar componentes sem interesse na etapa seguinte.

## M2.2 — Componentes conexos e morfologia

### Estratégia

A entrada do M2.2 é a máscara gerada no M2.1, lida sem depender de execução anterior. Primeiro, conto os componentes da máscara original; depois aplico **abertura** e **fechamento**, nessa ordem. As imagens antes, entre operações e após o tratamento são salvas separadamente. Por último, conto novamente os componentes e exporto áreas, caixas delimitadoras e centroides.

A abertura (erosão seguida de dilatação) ajuda a remover pontos isolados que foram classificados indevidamente como objeto. O fechamento (dilatação seguida de erosão) pode preencher pequenas falhas internas e unir interrupções curtas. Usei elemento estruturante **elíptico 3×3**, uma iteração por operação e área mínima de **20 pixels**. O filtro por área só define quais componentes são retidos, sem alterar o valor informado na coluna de contagem bruta.

### Comparação das conectividades e antes/depois

| Máscara analisada | Conectividade | Componentes brutos antes | Componentes retidos antes | Componentes brutos depois | Componentes retidos depois | Pixels brancos antes/depois |
|---|---:|---:|---:|---:|---:|---|
| Uniforme adaptativa | 4 | 37 | 8 | 12 | 8 | 18.686 / 18.638 |
| Uniforme adaptativa | 8 | 25 | 8 | 12 | 8 | 18.686 / 18.638 |
| Desigual adaptativa | 4 | 100 | 8 | 12 | 8 | 17.958 / 17.728 |
| Desigual adaptativa | 8 | 49 | 8 | 12 | 8 | 17.958 / 17.728 |
| Máscara diagonal de teste | 4 | 4 | 3 | 4 | 3 | 1.049 / 1.033 |
| Máscara diagonal de teste | 8 | 3 | 2 | 4 | 3 | 1.049 / 1.033 |

Os totais brutos variam porque a conectividade 8 também une pixels ligados na diagonal, enquanto a conectividade 4 considera apenas cima, baixo e lados. Nos discos, a diferença antes do tratamento aparece principalmente em fragmentos pequenos; depois da morfologia, os valores brutos passam a coincidir. **A contagem filtrada de oito discos nas cenas não quer dizer que cada rótulo represente perfeitamente um único objeto real**: isso precisa ser avaliado visualmente.

A máscara de teste `diagonal_demo_mask.png` deixa a diferença mais fácil de observar: dois quadrados que se encontram apenas pela diagonal são dois componentes na conectividade 4, mas um só na 8. A abertura separa esse contato, e as contagens finais coincidem. Isso ilustra também uma possível perda de ligação causada pela morfologia.

Na imagem desigual, o processamento alterou **536 pixels** no total e diminuiu a quantidade de componentes brutos. Mesmo assim ainda sobraram alguns componentes pequenos, porque a sequência 3×3 não elimina todos os fragmentos. Nos discos também se observa um efeito ruim: **alguns buracos escuros ficaram maiores depois da abertura**, pois a erosão retira pixels brancos ao redor deles. O fechamento 3×3 não é suficiente para recuperar buracos maiores. Outra limitação é que o fechamento pode juntar regiões que deveriam estar separadas. Portanto o ajuste da ordem e do elemento estruturante depende do defeito predominante na máscara.

### Medidas, validação e arquivos

Cada arquivo `*_before_components.csv` e `*_after_components.csv` lista os componentes sem incluir o fundo, com rótulo, área (pixels), `x`, `y`, largura, altura, centróide e marcação do filtro de área. Os arquivos `*_summary.json` guardam parâmetros, contagens brutas e filtradas, áreas, número de pixels brancos e quantidade de pixels modificados. Em cada estágio, **a soma das áreas brutas coincide com a quantidade de pixels brancos** da máscara correspondente.

As imagens com rótulos e caixas delimitadoras estão nos arquivos `*_before_labels.png` e `*_after_labels.png`. Para inspecionar uma sequência completa, abra `results/scene_uneven_c8_before.png`, `..._step_01_open.png`, `..._step_02_close.png` e `..._after.png`.

Os testes automatizados verificam limiar no valor exato, conectividades, medidas, máscaras vazias, objeto encostado à borda, parâmetros inválidos, arquivo ausente, máscara não binária e reexecução sem estado oculto. A execução preparada desta versão teve **13 testes aprovados**, registrados em `results/test_log.txt`. A biblioteca OpenCV faz a implementação dos operadores; o projeto realiza as escolhas dos parâmetros, a conferência e a interpretação das medidas.

## Considerações finais

As etapas mostram que a qualidade da máscara influencia diretamente a contagem posterior. Uma máscara com fundo incluído aumenta o número de componentes falsos, enquanto uma máscara com partes dos discos excluídas pode gerar fragmentos ou objetos incompletos. A morfologia ajuda em alguns defeitos, mas também pode mudar a estrutura original. Por isso o projeto conserva a máscara inicial, as etapas intermediárias e os resultados das duas conectividades.

## Referências

1. OpenCV, *Image Thresholding*. https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html
2. OpenCV, *Morphological Transformations*. https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html
3. OpenCV, *Structural Analysis and Shape Descriptors*. https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html
4. Contrato técnico complementar M2 e Rubrica dos laboratórios M2, documentos fornecidos com a atividade.

Declaração da assistência por IA: consultar `AI_USAGE.md`.
