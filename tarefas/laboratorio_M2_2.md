# Processamento de Imagens — 2026-02
## Laboratório M2.2 — Componentes conexos e sequência morfológica

### Objetivo

Ampliar **o mesmo código do M2.1** para limpar a máscara, rotular componentes conexos, contar objetos e justificar a ordem de uma sequência morfológica. O resultado final deve permitir rastrear a imagem original, a máscara inicial, cada operação e a contagem final.

### Regras

Atividade individual. OpenCV pode executar erosão, dilatação, abertura, fechamento, rotulação e estatísticas; não se exige implementação do zero. A operação `segment` da entrega anterior deve continuar executável. Use o contrato técnico complementar da M2 para interface, estrutura, relatórios e testes. Não confunda componentes detectados com a quantidade real de objetos quando há contato, sobreposição ou fragmentação.

### Atividades obrigatórias

1. **Partir da máscara do M2.1.** Carregue uma máscara binária produzida pelo próprio projeto ou reproduza a segmentação por comando documentado. Preserve uma cópia da máscara inicial e identifique se o objeto está em branco (255) e o fundo em preto (0).
2. **Rotular a máscara inicial.** Conte componentes de primeiro plano usando conectividade 4 e 8 **na mesma máscara**, com parâmetros iguais. Informe a quantidade de componentes em cada caso, excluindo o rótulo de fundo. Para cada componente da conectividade escolhida para a análise final, exporte rótulo, área em pixels, caixa delimitadora (`x`, `y`, `largura`, `altura`) e centroide (`cx`, `cy`) em CSV. Explique diferenças entre as conectividades, se houver.
3. **Montar sequência morfológica justificada.** Aplique pelo menos **duas operações em sequência**, incluindo obrigatoriamente abertura ou fechamento e pelo menos mais uma operação escolhida conforme os defeitos observados (por exemplo, abertura seguida de fechamento). Informe forma e tamanho do elemento estruturante, número de iterações e ordem. Salve a saída de cada estágio. Justifique separadamente o problema visado por cada operação e observe se houve perda de detalhes, fusão de objetos ou mudança de contorno. Operações repetidas com os mesmos parâmetros sem finalidade distinta não satisfazem a sequência.
4. **Recontar e comparar.** Execute a rotulação na máscara final. Gere o CSV final, uma imagem de rótulos/caixas visualizável e uma tabela antes/depois com número de componentes, área total do primeiro plano e ao menos duas observações sobre mudanças. Defina um critério explícito de filtragem por área, se empregado; registre contagens brutas e após filtro. Aplique o mesmo critério nas comparações pertinentes e não trate o rótulo de fundo como objeto.
5. **Avaliar limitações.** Use ao menos duas imagens com comportamentos diferentes, incluindo uma com componentes pequenos ou contato entre regiões. Descreva ao menos um caso em que a sequência ajuda e um em que pode prejudicar ou não resolver a separação. Watershed, contornos e classificação ficam como extensões opcionais; não substituem a rotulação e a sequência obrigatórias.

### Interface mínima

No mesmo `pdi_lab`, mantenha `segment` e acrescente `analyze`:

```bash
pdi_lab --input images/output/cena_mask.png --output results/cena \
  --operation analyze --connectivity 8 --min-area 20
```

Em `analyze`, `--input` é a máscara binária e `--output` é um **prefixo**: crie, por exemplo, `results/cena_initial.csv`, `results/cena_final.csv`, `results/cena_labels.png` e `results/cena_summary.json` (ou equivalente documentado). Os estágios morfológicos devem ser salvos em PNG com nomes definidos no `README.md`. `--connectivity` aceita 4 ou 8, com padrão documentado; `--min-area` é opcional, inteiro não negativo, e o CSV deve indicar se o componente foi mantido pelo filtro. Documente os parâmetros morfológicos por argumentos ou arquivo de configuração incluído na entrega, sem exigir edição do código para reproduzir outro caso.

CSV mínimo:

```text
label,area,x,y,width,height,cx,cy,kept
1,42,5,7,8,9,8.4,10.6,true
```

A numeração dos rótulos não precisa coincidir entre bibliotecas ou entre máscaras. O fundo, normalmente rótulo 0, não entra no CSV de objetos. O arquivo de resumo deve guardar conectividade, parâmetros da sequência, contagens brutas e filtradas, e áreas totais antes/depois.

### Testes mínimos

- Máscara sintética com dois pixels apenas na diagonal: conte 2 componentes em conectividade 4 e 1 em conectividade 8.
- Máscara sintética com ruído isolado e uma região principal: verifique o efeito previsto da abertura; teste um furo pequeno para o fechamento, se essa operação for escolhida.
- Máscara vazia (contagem zero), objeto que toca a borda e parâmetro `--connectivity` inválido.
- Reexecução das duas imagens do estudo, com saídas intermediárias e CSV; confira que a soma das áreas dos componentes brutos corresponde à quantidade de pixels de primeiro plano da máscara respectiva, antes de qualquer filtro.

### Mini relatório `REPORT.md`

Acrescente uma seção M2.2 ao relatório anterior, sem apagar a M2.1. Apresente a sequência com seus parâmetros, figuras lado a lado por estágio, tabela de componentes antes/depois, explicação de 4 versus 8, justificativa das escolhas e análise de pelo menos um efeito indesejado. Explique se a contagem se aproxima da interpretação humana e por que não equivale necessariamente ao número real de objetos. Uma máscara de referência ou contagem manual pode sustentar medidas adicionais, mas deve ter origem documentada.

### Entrega consolidada

Envie uma versão atualizada do mesmo projeto com as operações `segment` e `analyze`, imagens, resultados, testes, `README.md`, `REPORT.md`, `AI_USAGE.md` e `lab.json`. Não envie dois códigos independentes. Preserve os comandos necessários para reproduzir a M2.1 e a M2.2. A evidência parcial e a avaliação seguem a rubrica vigente; o professor informará os prazos no ambiente de entrega.
