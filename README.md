# Laboratórios de Processamento de Imagens — M2

**Aluno:** Victor Hugo Chrisosthemos Teixeira  
**Disciplina:** Processamento de Imagens — 2026/02  
**Linguagem:** Python  
**Bibliotecas:** OpenCV e NumPy

Este repositório reúne os trabalhos desenvolvidos na disciplina de Processamento de Imagens. A pasta [`M2/`](M2/) contém a implementação dos laboratórios **M2.1 — Máscara Binária e Segmentação** e **M2.2 — Componentes Conexos e Morfologia**, utilizando um único projeto executado pela linha de comando.

## Objetivos

**M2.1 — Segmentação:** produzir máscaras binárias a partir de imagens, comparando limiarização fixa e adaptativa. O projeto permite avaliar a influência da iluminação, do fundo e dos parâmetros na identificação das regiões de interesse.

**M2.2 — Análise de componentes:** utilizar as máscaras do M2.1 para identificar componentes conexos nas conectividades 4 e 8, aplicar abertura e fechamento morfológico, medir regiões e comparar os resultados antes e depois do processamento.

As máscaras utilizam **branco (255) para primeiro plano** e **preto (0) para fundo**. Os componentes identificados representam regiões conectadas da imagem, não necessariamente objetos distintos do mundo real.

## Estrutura do repositório

```text
laboratorio_M2_processamento_de_imagens/
├── README.md                # Apresentação geral (este arquivo)
├── M2/
│   ├── pdi_lab/             # Código das operações segment e analyze
│   ├── images/
│   │   ├── input/           # Imagens de entrada
│   │   ├── reference/       # Referências para testes sintéticos
│   │   └── output/          # Máscaras e comparações
│   ├── results/             # Imagens, CSVs e resumos JSON
│   ├── tests/               # Testes automatizados
│   ├── tools/               # Scripts de reprodução dos resultados
│   ├── requirements.txt     # Dependências
│   ├── lab.json             # Identificação da entrega
│   ├── README.md            # Instruções técnicas completas
│   ├── REPORT.md            # Análise e discussão dos resultados
│   ├── AI_USAGE.md          # Registro de uso de IA
│   └── FOTOS_FONTES.md      # Origem das fotografias
└── tarefas/                 # Outras atividades da disciplina
```

## Como executar

É necessário **Python 3.10 ou superior**. No terminal, entre na pasta do projeto:

```bash
cd M2
python -m pip install -r requirements.txt
```

No Windows, caso `python` não funcione, utilize `py` no lugar. É recomendável instalar as dependências em um ambiente virtual. A execução não depende de notebook ou interface gráfica.

### 1. Segmentação — M2.1

**Limiarização fixa:**

```bash
python -m pdi_lab --operation segment --input images/input/foto_moedas.png --output images/output/foto_moedas_fixed.png --method fixed --threshold 120 --foreground light
```

**Limiarização adaptativa:**

```bash
python -m pdi_lab --operation segment --input images/input/foto_moedas.png --output images/output/foto_moedas_adaptive.png --method adaptive --block-size 75 --c -4 --foreground light
```

Esses comandos geram máscaras PNG binárias e arquivos JSON com os parâmetros e a quantidade de pixels de primeiro plano.

### 2. Componentes conexos e morfologia — M2.2

**Conectividade 4:**

```bash
python -m pdi_lab --operation analyze --input images/output/foto_moedas_fixed.png --output results/foto_moedas_c4 --connectivity 4 --min-area 20 --sequence open,close --kernel-size 3 --kernel-shape ellipse --iterations 1
```

**Conectividade 8:**

```bash
python -m pdi_lab --operation analyze --input images/output/foto_moedas_fixed.png --output results/foto_moedas_c8 --connectivity 8 --min-area 20 --sequence open,close --kernel-size 3 --kernel-shape ellipse --iterations 1
```

O programa salva as máscaras intermediárias, as imagens com identificação de componentes, tabelas CSV com medidas (área, caixa delimitadora e centroide) e um resumo JSON.

### 3. Reproduzir todos os resultados e executar os testes

```bash
python tools/reproduce.py
python -m unittest discover -s tests -v
```

O primeiro comando recria os resultados a partir das entradas presentes na pasta `images/input/`. O segundo executa os testes automatizados.

## Exemplos de resultados

**Comparação de segmentação — fotografia de moedas:**

![Comparação entre limiarização fixa e adaptativa](M2/images/output/foto_moedas_comparacao.png)

**Comparação antes e depois da análise morfológica:**

![Comparação de componentes e morfologia](M2/results/foto_moedas_c8_comparison.png)

As imagens usadas no estudo incluem fotografias de exemplo de terceiros (`foto_moedas.png` e `foto_xicara.png`) e cenas sintéticas utilizadas nos testes. A origem e as condições de uso estão documentadas em [`FOTOS_FONTES.md`](M2/FOTOS_FONTES.md).

## Documentação da entrega

- [Instruções técnicas e demais comandos](M2/README.md)
- [Relatório M2.1 e M2.2](M2/REPORT.md)
- [Registro de uso de IA](M2/AI_USAGE.md)
- [Fontes das fotografias](M2/FOTOS_FONTES.md)

## Referências

- [OpenCV — Image Thresholding](https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html)
- [OpenCV — Morphological Transformations](https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html)
- [OpenCV — Structural Analysis and Shape Descriptors](https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html)

---

Projeto acadêmico desenvolvido para a disciplina de Processamento de Imagens.
