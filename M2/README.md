# Processamento de Imagens — M2.1 e M2.2

**Estudante:** Victor Hugo Chrisosthemos Teixeira  
**Disciplina:** Processamento de Imagens — 2026/02  
**Pasta para o repositório:** `M1_2/` (solicitada para publicação; as etapas acadêmicas são **M2.1** e **M2.2**).

## O que este projeto faz

O **mesmo programa** implementa `segment` (M2.1) e `analyze` (M2.2), por linha de comando, usando Python e OpenCV. Segmentação produz máscara binária PNG; análise identifica componentes conexos, compara 4 e 8 vizinhos, aplica abertura e fechamento, salva PNGs, CSVs e resumo JSON.

**Alvo:** regiões de maior intensidade luminosa, aproximadamente circulares, em fotografias de moedas e de xícara/pires. São objetos de tipos distintos, usados para demonstrar a sensibilidade dos métodos ao fundo; o algoritmo não classifica tipos de objetos. Os exemplos sintéticos controlados também apresentam discos, neste caso escuros sobre fundo claro. **Branco (255) sempre significa primeiro plano; preto (0) é fundo.**

Há **duas fotografias reais independentes** de amostras públicas em `images/input/foto_moedas.png` e `images/input/foto_xicara.png`, além de duas cenas geradas e uma máscara para teste de conectividade. A origem das fotos está em [FOTOS_FONTES.md](FOTOS_FONTES.md). As fotografias não foram feitas pelo aluno; as imagens sintéticas são explicitamente artificiais.

## Instalação

Requer Python 3.10+ com `pip`, sem Colab, notebook, IDE ou interface gráfica.

No terminal, entre na pasta `M1_2` e execute:

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

Nos exemplos seguintes, `python` representa o Python do ambiente virtual (ou outro com as dependências instaladas). `requirements.txt` declara `opencv-python-headless>=4.8,<5` (fornece `cv2`) e `numpy>=1.26,<3`. Os resultados fornecidos foram gerados com **Python 3.13.5**, **OpenCV 4.13.0** e **NumPy 2.3.5**. Não é necessário instalar scikit-image: as duas fotografias já estão incluídas.

## M2.1 — segmentação

As duas configurações (`fixed` e `adaptive`) devem ser comparadas **em cada uma** das imagens. A CLI também aceita `otsu` como terceira opção. O limiar fixo é aplicado ao cinza; o adaptativo utiliza média gaussiana local.

**Fotografia de moedas, objeto claro (configurações usadas no relatório):**

```bash
python -m pdi_lab --operation segment --input images/input/foto_moedas.png --output images/output/foto_moedas_fixed.png --method fixed --threshold 120 --foreground light
python -m pdi_lab --operation segment --input images/input/foto_moedas.png --output images/output/foto_moedas_adaptive.png --method adaptive --block-size 75 --c -4 --foreground light
```

**Fotografia da xícara e pires, fundo texturizado:**

```bash
python -m pdi_lab --operation segment --input images/input/foto_xicara.png --output images/output/foto_xicara_fixed.png --method fixed --threshold 170 --foreground light
python -m pdi_lab --operation segment --input images/input/foto_xicara.png --output images/output/foto_xicara_adaptive.png --method adaptive --block-size 75 --c -4 --foreground light
```

**Exemplo controlado de discos escuros, com polaridade invertida:**

```bash
python -m pdi_lab --operation segment --input images/input/scene_uniform.png --output images/output/scene_uniform_fixed.png --method fixed --threshold 120 --foreground dark
python -m pdi_lab --operation segment --input images/input/scene_uniform.png --output images/output/scene_uniform_adaptive.png --method adaptive --block-size 75 --c 8 --foreground dark
```

`--input` e `--output` são relativos à raiz do projeto (caminhos absolutos não são necessários). A máscara é gravada **no caminho exato** de `--output`, com extensão `.png`, mesmas dimensões, 1 canal, somente valores 0 e 255. Um arquivo JSON com mesmo nome-base registra parâmetros e pixels de primeiro plano. O pré-processamento se limita à **conversão para cinza**, sem suavização; a inversão é controlada por `--foreground dark` ou `light`.

## M2.2 — componentes conexos e morfologia

A configuração selecionada para as duas fotografias foi o **limiar fixo** (a alternativa adaptativa amplificou texturas do fundo). A máscara gerada pelo M2.1 entra diretamente no M2.2, sem estado oculto.

```bash
python -m pdi_lab --operation analyze --input images/output/foto_moedas_fixed.png --output results/foto_moedas_c4 --connectivity 4 --min-area 20 --sequence open,close --kernel-size 3 --kernel-shape ellipse --iterations 1
python -m pdi_lab --operation analyze --input images/output/foto_moedas_fixed.png --output results/foto_moedas_c8 --connectivity 8 --min-area 20 --sequence open,close --kernel-size 3 --kernel-shape ellipse --iterations 1
python -m pdi_lab --operation analyze --input images/output/foto_xicara_fixed.png --output results/foto_xicara_c4 --connectivity 4 --min-area 20 --sequence open,close --kernel-size 3 --kernel-shape ellipse --iterations 1
python -m pdi_lab --operation analyze --input images/output/foto_xicara_fixed.png --output results/foto_xicara_c8 --connectivity 8 --min-area 20 --sequence open,close --kernel-size 3 --kernel-shape ellipse --iterations 1
```

`--connectivity` aceita **4 ou 8**. `--min-area` aceita inteiro **não negativo** (0 desativa a filtragem por área). A comparação de conectividades usa a **mesma máscara**; o filtro afeta apenas o campo `kept` e a contagem filtrada, mantendo os componentes brutos no CSV. A morfologia exige duas operações diferentes, com sequência padrão `open,close`. São aceitos `close,open`, formas `ellipse`, `rect`, `cross`, kernels ímpares e iterações positivas.

`--output` do `analyze` é **prefixo**, e não caminho de um arquivo só. Para `results/foto_moedas_c4`, o projeto grava:

| Sufixo | Conteúdo |
|---|---|
| `_before.png`, `_after.png` | máscara inicial e final |
| `_step_01_open.png`, `_step_02_close.png` | resultados intermediários |
| `_before_labels.png`, `_after_labels.png` | componentes coloridos e caixas |
| `_before_components.csv`, `_after_components.csv` | medidas e filtro dos componentes |
| `_comparison.png` | antes e depois lado a lado |
| `_summary.json` | parâmetros, totais brutos e filtrados, áreas e pixels alterados |

Os CSVs contêm o cabeçalho exato: `label,area,x,y,width,height,cx,cy,kept`. O fundo (rótulo 0) é excluído; `kept` vale `true` ou `false`. Os centroides estão em pixels e podem possuir decimais.

## Reprodução integral e testes

```bash
python tools/reproduce.py
python -m unittest discover -s tests -v
```

O primeiro comando **recria todas as máscaras e análises** a partir dos arquivos de entrada, incluindo sintéticos, fotografias e resultados de 4/8; as fotos originais não são geradas ou sobrescritas. O segundo executa testes automatizados. Para atualizar as cenas sintéticas originais separadamente: `python tools/generate_inputs.py`.

Em `images/output/foto_moedas_comparacao.png` e `foto_xicara_comparacao.png` aparecem original, limiar fixo, adaptativo e visualização de divergências. **Ciano** = apenas fixo; **magenta** = apenas adaptativo. Sem uma máscara de referência para as fotografias, isso **não é medição de falso positivo/negativo**. Já as cenas sintéticas possuem referências em `images/reference` e mapas de erros em `images/output/scene_*_errors.png`.

Os testes controlam pixels no limiar, máscaras binárias, dimensões, conectividade, casos vazios, bordas, morfologia, CSVs, arquivos ausentes e parâmetros inválidos. O programa retorna código **0** em sucesso e diferente de **0** em erro.

## Organização

```text
M1_2/
├── README.md / REPORT.md / AI_USAGE.md / FOTOS_FONTES.md
├── lab.json / requirements.txt / .gitignore
├── pdi_lab/              # mesmo código para as duas operações
├── tools/                # geração dos sintéticos e reprodução
├── tests/                # testes automatizados
├── images/
│   ├── input/            # imagens originais (fotos + sintéticas)
│   ├── reference/        # referência APENAS das sintéticas
│   └── output/           # máscaras, metadados e comparações
└── results/              # PNG, CSV, JSON, logs
```

Para submeter pelo GitHub, adicione a pasta inteira `M1_2/` ao repositório. Não envie `.venv`, caches ou binários. Confirme também a exigência de informar o **link do repositório no ambiente acadêmico**; o ZIP não publica arquivos automaticamente.

## Referências

- OpenCV, *Image Thresholding*: https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html
- OpenCV, *Morphological Transformations*: https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html
- OpenCV, *Structural Analysis and Shape Descriptors*: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html
- skimage, documentação das fotos de exemplo: https://scikit-image.org/docs/stable/api/skimage.data.html
- Enunciados M2.1 e M2.2, contrato técnico complementar da M2 e rubrica enviados com a atividade.
