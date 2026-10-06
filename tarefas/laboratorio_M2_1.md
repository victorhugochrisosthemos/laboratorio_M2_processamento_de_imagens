# Processamento de Imagens — 2026-02
## Laboratório M2.1 — Máscara binária e segmentação

### Objetivo

Produzir e avaliar uma máscara binária de uma classe de objetos em imagens digitais, explicitando a escolha do método, os parâmetros e os erros de segmentação. Este é o primeiro marco de **um único projeto de código** que será ampliado no M2.2.

### Regras

Atividade individual. São permitidas funções prontas do OpenCV para leitura, conversão de cor, filtros, limiarização e operações necessárias à segmentação. C++, Java ou Python são aceitos. Preserve o contrato técnico comum da M1 para portabilidade, linha de comando, arquivos, testes e documentação, observando as adaptações da M2 descritas no contrato complementar. A solução deve executar localmente fora do Colab e não pode consistir apenas em notebook. Não é exigida implementação manual dos algoritmos do OpenCV.

### Atividades obrigatórias

1. **Definir o alvo.** Identifique o que vale como objeto de interesse e escolha ao menos duas imagens de entrada: uma com condições favoráveis e outra que apresente uma dificuldade real (iluminação, fundo, cor, sombra ou ruído). Mantenha os originais sem alterações. Uma delas deve conter mais de um objeto discernível para permitir a etapa M2.2. Use imagens fornecidas ou próprias com permissão de uso.
2. **Gerar máscara por dois ajustes comparáveis.** No mesmo conjunto de imagens, execute um limiar fixo em cinza e pelo menos uma segunda configuração: Otsu, limiarização adaptativa ou seleção de intervalo em HSV. Registre método e parâmetros. Se o objeto for escuro, documente a inversão aplicada. É permitido pré-processar a imagem, mas a comparação deve identificar esse pré-processamento.
3. **Selecionar a configuração de trabalho.** Explique qual máscara será usada no M2.2 e por quê, indicando acertos e falsos positivos/falsos negativos visíveis. Apresente a imagem original, as duas máscaras e ao menos uma sobreposição/visualização que permita localizar os erros. Para o mesmo caso de entrada, indique os parâmetros das duas configurações.
4. **Salvar e validar as saídas.** A máscara final deve manter largura e altura da imagem de entrada, ter um canal e conter somente 0 (fundo) e 255 (objeto). A saída deve ser PNG ou outro formato sem perdas; não use JPEG para a máscara. Registre contagem de pixels de primeiro plano ou sua proporção e confirme programaticamente o caráter binário.

### Interface mínima

Um único executável/módulo `pdi_lab`, com a operação `segment`:

```bash
pdi_lab --input images/input/cena.png --output images/output/cena_mask.png \
  --operation segment --method fixed --threshold 120
```

`--method` aceita `fixed`, `otsu`, `adaptive` ou `hsv`. Ofereça obrigatoriamente `fixed` e pelo menos um dos outros métodos. Documente os parâmetros usados pela implementação escolhida (`--threshold`, intervalos HSV, tamanho de bloco, constante etc.). `--input`, `--output` e `--operation` seguem o contrato existente. Os comandos concretos, inclusive a segunda configuração, devem constar no `README.md`. Caso o segundo método use HSV, indique os limites no intervalo adotado pela biblioteca e trate separadamente faixas que cruzem a descontinuidade do matiz, se isso ocorrer no objeto escolhido.

### Testes mínimos

- Imagem pequena sintética com resultado previsível para o limiar fixo, incluindo pixels no limiar e dos dois lados dele.
- As duas imagens reais, processadas pelas duas configurações; identificação de ao menos um erro ou limitação observável.
- Falha de leitura, método desconhecido e parâmetro inválido quando aplicável; sucesso com código de saída 0, falha com código diferente de 0.
- Verificação automática de dimensões, canal único e conjunto de valores `{0, 255}` na máscara final.

### Mini relatório `REPORT.md`

Descreva alvo, imagens, configurações e parâmetros, justificativa do pré-processamento, tabela pequena com proporção de primeiro plano por imagem/configuração, figuras com legendas e discussão comparativa. Responda: (a) em que casos o limiar fixo falhou ou funcionou; (b) qual parâmetro foi mais sensível; (c) quais erros podem atrapalhar a contagem de objetos no M2.2. Distingua observação visual de uma métrica quantitativa: sem máscara de referência, não declare acurácia, precisão ou revocação.

