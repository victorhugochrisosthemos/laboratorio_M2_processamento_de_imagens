# Laboratório M2.1 — máscara binária e segmentação

Projeto em Python/OpenCV para segmentar traços escuros de escrita em imagens de páginas. O alvo é o conjunto de pixels pertencentes a caracteres e símbolos escuros; o restante é tratado como fundo.

Foram comparadas duas configurações sobre as mesmas imagens:

- limiar fixo em cinza, `T = 115`, com inversão;
- limiar adaptativo Gaussiano, `block-size = 31`, `C = 8`, também com inversão.

Nos dois casos é aplicado antes um filtro Gaussiano `3x3`. A máscara final escolhida para continuidade no M2.2 é a adaptativa.

## Estrutura

```text
pdi_lab_m21/
├── pdi_lab.py
├── pyproject.toml
├── requirements.txt
├── README.md
├── REPORT.md
├── IMAGE_SOURCES.md
├── images/
│   ├── input/
│   │   ├── printed_page.png
│   │   └── handwritten_notes.png
│   └── output/
│       ├── *_fixed.png
│       ├── *_adaptive.png
│       ├── *_mask.png
│       ├── *_overlay.png
│       ├── *_comparison.png
│       └── *_stats.json
└── tests/
    └── test_pdi_lab.py
```

## Instalação

Requer Python 3.10 ou superior.

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

Depois da instalação editável, o comando `pdi_lab` fica disponível. Também é possível executar diretamente com `python pdi_lab.py`.

## Comandos usados no experimento

### Página impressa — limiar fixo

```bash
pdi_lab --input images/input/printed_page.png \
  --output images/output/printed_page_fixed.png \
  --operation segment --method fixed \
  --threshold 115 --invert --blur-ksize 3 \
  --overlay images/output/printed_page_fixed_overlay.png \
  --stats-json images/output/printed_page_fixed_stats.json
```

### Página impressa — limiar adaptativo

```bash
pdi_lab --input images/input/printed_page.png \
  --output images/output/printed_page_adaptive.png \
  --operation segment --method adaptive \
  --invert --blur-ksize 3 --block-size 31 --c 8 \
  --overlay images/output/printed_page_adaptive_overlay.png \
  --stats-json images/output/printed_page_adaptive_stats.json
```

### Anotações manuscritas — limiar fixo

```bash
pdi_lab --input images/input/handwritten_notes.png \
  --output images/output/handwritten_notes_fixed.png \
  --operation segment --method fixed \
  --threshold 115 --invert --blur-ksize 3 \
  --overlay images/output/handwritten_notes_fixed_overlay.png \
  --stats-json images/output/handwritten_notes_fixed_stats.json
```

### Anotações manuscritas — limiar adaptativo

```bash
pdi_lab --input images/input/handwritten_notes.png \
  --output images/output/handwritten_notes_adaptive.png \
  --operation segment --method adaptive \
  --invert --blur-ksize 3 --block-size 31 --c 8 \
  --overlay images/output/handwritten_notes_adaptive_overlay.png \
  --stats-json images/output/handwritten_notes_adaptive_stats.json
```

## Parâmetros disponíveis

`--method` aceita `fixed`, `otsu`, `adaptive` e `hsv`.

Para `fixed`, o principal parâmetro é `--threshold`. Para `adaptive`, são usados `--block-size` e `--c`. `--invert` é necessário neste experimento porque os traços de interesse são mais escuros que o fundo. `--blur-ksize` controla o filtro Gaussiano; `0` desativa o filtro.

O modo `hsv` aceita `--h-min`, `--h-max`, `--s-min`, `--s-max`, `--v-min` e `--v-max`. Se `h-min > h-max`, a implementação divide automaticamente a faixa do matiz em `[h-min, 179]` e `[0, h-max]`, cobrindo a descontinuidade do HSV do OpenCV.

A saída de máscara é recusada quando a extensão é JPEG. PNG, BMP e TIFF são aceitos.

## Validação

Ao final de cada execução, o programa verifica:

- mesma largura e altura da entrada;
- um único canal;
- valores restritos a `0` e `255`;
- proporção e quantidade de pixels de primeiro plano.

Exemplo de saída:

```text
method=adaptive foreground_pixels=12756 foreground_ratio=0.173920 binary=True output=images/output/printed_page_adaptive.png
```

## Testes

```bash
pytest
```

Os testes cobrem o caso sintético com pixels abaixo, no e acima do limiar, as duas imagens reais com os dois ajustes principais, leitura inválida, método desconhecido, parâmetro fora do intervalo, rejeição de JPEG e validação automática da máscara.

As fontes e condições de reutilização das imagens estão em `IMAGE_SOURCES.md`.
