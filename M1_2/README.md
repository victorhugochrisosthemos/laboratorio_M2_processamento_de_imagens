# Laboratórios M2.1 e M2.2 — Processamento de Imagens

**Aluno:** Victor Hugo Chrisosthemos Teixeira  
**Disciplina:** Processamento de Imagens — 2026/02  
**Organização no repositório:** `M1_2/` 

O mesmo projeto executa as duas etapas:

- **M2.1 — `segment`:** identifica discos escuros em imagens, gerando máscara PNG de um canal, com branco para o objeto (255) e preto para o fundo (0). Foram comparados limiar fixo e adaptativo gaussiano em duas imagens; Otsu também está disponível.
- **M2.2 — `analyze`:** rotula componentes de uma máscara binária, compara conectividades 4 e 8 e executa abertura seguida de fechamento morfológico. Exporta imagens intermediárias, tabelas CSV e resumo JSON.

Os exemplos são **imagens sintéticas** do projeto, com iluminação uniforme e desigual. Não representam fotografias coletadas fora do programa. Suas máscaras de referência possibilitam examinar erros de inclusão e exclusão.

## Instalação e execução

É necessário ter **Python 3.10 ou superior**, pip e acesso ao terminal. Não é necessário notebook, IDE nem interface gráfica. Instale a partir da pasta `M1_2`.

**Windows (PowerShell):**

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pdi_lab --help
```

**Linux/macOS:**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pdi_lab --help
```

Nos comandos abaixo, `python` significa o Python do ambiente criado (no Windows, `.venv\Scripts\python.exe`; no Linux/macOS, `.venv/bin/python`). Também é possível ativar o ambiente e usar `python` normalmente.

Dependências declaradas em `requirements.txt`: **opencv-python-headless >= 4.8, < 5** (fornece `cv2`, o OpenCV sem GUI) e **numpy >= 1.26, < 3**. A execução usada para gerar os resultados inclusos foi testada com **OpenCV 4.13.0, NumPy 2.3.5 e Python 3.13.5**. Outras versões compatíveis podem causar pequenas diferenças em resultados numéricos ou rótulos de componentes.

## M2.1: segmentação

Primeiro exemplo, limiar fixo (120) com objeto escuro:

```bash
python -m pdi_lab --operation segment --input images/input/scene_uniform.png --output images/output/scene_uniform_fixed.png --method fixed --threshold 120 --foreground dark
```

Segundo exemplo, limiar adaptativo gaussiano (janela 75, C=8):

```bash
python -m pdi_lab --operation segment --input images/input/scene_uneven.png --output images/output/scene_uneven_adaptive.png --method adaptive --block-size 75 --c 8 --foreground dark
```

Uma terceira alternativa disponível, sem exigência de uso:

```bash
python -m pdi_lab --operation segment --input images/input/scene_uniform.png --output images/output/teste_otsu.png --method otsu --foreground dark
```

Para comparar as duas configurações nas duas imagens, execute `python tools/reproduce.py`. A máscara é salva **exatamente** em `--output`, em PNG de um canal e valores 0/255. É gerado também um JSON de parâmetros no mesmo nome, com extensão `.json`.

`--foreground dark` indica discos escuros em fundo claro; `--foreground light` inverte a interpretação. Para o limiar fixo com objetos escuros, intensidade **menor ou igual** ao limiar passa a branco na máscara, como verificado nos testes.

## M2.2: componentes e morfologia

**A mesma máscara, primeiro com conectividade 4, depois com 8:**

```bash
python -m pdi_lab --operation analyze --input images/output/scene_uneven_adaptive.png --output results/manual_c4 --connectivity 4 --min-area 20 --sequence open,close --kernel-size 3 --kernel-shape ellipse --iterations 1
python -m pdi_lab --operation analyze --input images/output/scene_uneven_adaptive.png --output results/manual_c8 --connectivity 8 --min-area 20 --sequence open,close --kernel-size 3 --kernel-shape ellipse --iterations 1
```

Para um caso controlado com objetos que se tocam apenas na diagonal:

```bash
python -m pdi_lab --operation analyze --input images/input/diagonal_demo_mask.png --output results/diagonal_c4 --connectivity 4 --min-area 20
python -m pdi_lab --operation analyze --input images/input/diagonal_demo_mask.png --output results/diagonal_c8 --connectivity 8 --min-area 20
```

A saída `--output` da análise é **um prefixo**, e não o nome de um único arquivo. Exemplo, prefixo `results/manual_c4`:

| Arquivo | Conteúdo |
|---|---|
| `manual_c4_before.png` | Máscara original (sem alterações) |
| `manual_c4_step_01_open.png` | Máscara após abertura |
| `manual_c4_step_02_close.png` | Máscara após fechamento |
| `manual_c4_after.png` | Máscara final |
| `manual_c4_before_labels.png` e `manual_c4_after_labels.png` | Rótulos coloridos e caixas dos componentes retidos |
| `manual_c4_comparison.png` | Antes à esquerda e depois à direita |
| `manual_c4_before_components.csv` e `manual_c4_after_components.csv` | Componentes brutos, suas medidas e coluna `retained` para o filtro de área |
| `manual_c4_summary.json` | Parâmetros, áreas, pixels, contagens brutas/filtradas e diferenças |

Os CSVs têm sempre as colunas: `stage`, `component_id`, `area`, `x`, `y`, `width`, `height`, `centroid_x`, `centroid_y`, `retained`. As coordenadas são de pixels; a caixa delimitadora informa largura e altura, e o centróide é o ponto médio calculado a partir dos pixels do componente. O filtro mantém componentes com `area >= min-area` e **não elimina dados da contagem bruta**, que permanece no CSV. O rótulo zero (fundo) nunca é incluído na contagem.

A sequência padrão é **abertura → fechamento**, com elemento estruturante elíptico 3×3 e uma iteração por operação. Também é possível usar `--sequence close,open`, `--kernel-shape rect|cross` e outros tamanhos ímpares. O relatório comenta vantagens e perdas observadas.

## Reproduzir os experimentos e rodar testes

Na pasta `M1_2`, executar:

```bash
python tools/reproduce.py
python -m unittest discover -s tests -v
```

O primeiro comando gera novamente os arquivos em `images/input`, `images/reference`, `images/output` e `results`, inclusive os pares conectividade 4/8. A geração utiliza semente fixa para o ruído, de forma que os exemplos sejam repetíveis. O segundo comando testa limiar no valor exato, métodos, conectividades, áreas, caixas, máscara vazia, ruído, entrada inválida, erros na CLI e exportação.

Para executar só a geração das imagens (sem análises): `python tools/generate_inputs.py`.

**Visualização dos erros da segmentação:** `images/output/scene_uniform_errors.png` e `scene_uneven_errors.png`; à esquerda está o resultado do limiar fixo e à direita o adaptativo. **Vermelho** indica inclusão indevida de fundo na máscara e **azul** indica região do objeto que ficou fora. Os erros são avaliados contra as referências artificiais em `images/reference/`, não contra uma anotação externa.

## Estrutura do projeto

```text
M1_2/
├── README.md
├── REPORT.md
├── AI_USAGE.md
├── lab.json
├── requirements.txt
├── pdi_lab/
│   ├── __init__.py
│   ├── __main__.py
│   └── core.py
├── tools/
│   ├── generate_inputs.py
│   └── reproduce.py
├── tests/
│   └── test_lab.py
├── images/
│   ├── input/
│   ├── reference/
│   └── output/
└── results/
```

As pastas `.venv`, `__pycache__` e demais arquivos gerados pelo ambiente são ignorados no `.gitignore`.

## Limites e verificação antes da entrega

O trabalho foi organizado usando o **contrato complementar da M2** e a **rubrica dos laboratórios M2** fornecidos. Os enunciados individuais completos dos Labs M2.1 e M2.2 **não foram anexados**: antes de entregar, compare os exemplos e os nomes de saídas com o texto integral dos dois enunciados disponibilizados na disciplina. O relato parcial anterior do M2.1, quando aplicável, é verificado pelo professor e não foi inventado nem incluído como entrega retroativa.

## Referências técnicas

1. OpenCV, *Image Thresholding*, documentação oficial: https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html
2. OpenCV, *Morphological Transformations*, documentação oficial: https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html
3. OpenCV, *Structural Analysis and Shape Descriptors* (`connectedComponentsWithStats`), documentação oficial: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html
