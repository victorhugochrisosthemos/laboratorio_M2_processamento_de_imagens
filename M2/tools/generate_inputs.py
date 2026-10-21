"""Cria imagens sintéticas controladas e suas máscaras de referência.

As imagens não representam fotografias reais. A referência marca os oito discos
pretendidos, permitindo visualizar inclusões e exclusões da segmentação.
"""
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
HEIGHT, WIDTH = 240, 360
DISCS = [(56, 62, 26), (137, 63, 28), (220, 66, 27), (304, 62, 26),
         (62, 168, 30), (145, 170, 27), (226, 167, 29), (307, 169, 27)]


def generate(name: str, uneven: bool) -> None:
    rng = np.random.default_rng(2026 + int(uneven))
    if uneven:
        # A região à esquerda fica escura mesmo sem fazer parte dos objetos.
        background = np.linspace(108, 230, WIDTH, dtype=np.float32)[None, :]
        image = np.repeat(background, HEIGHT, axis=0)
        image += 8 * np.cos(np.linspace(-np.pi, np.pi, HEIGHT))[:, None]
    else:
        image = np.full((HEIGHT, WIDTH), 217.0, dtype=np.float32)
    image += rng.normal(0, 2.2, size=(HEIGHT, WIDTH))
    reference = np.zeros((HEIGHT, WIDTH), dtype=np.uint8)

    for index, (x, y, radius) in enumerate(DISCS):
        cv2.circle(reference, (x, y), radius, 255, -1)
        mask = np.zeros_like(reference)
        cv2.circle(mask, (x, y), radius, 255, -1)
        image[mask == 255] = 62 + (index % 3) * 6 + rng.normal(
            0, 3, size=int(np.count_nonzero(mask)))

    # Marcas claras e pequenas manchas escuras, que desafiam os métodos.
    for x, y in [(53, 62), (220, 65), (305, 170)]:
        cv2.circle(image, (x, y), 3, 190, -1)
    for x, y in [(14, 21), (112, 119), (275, 115), (336, 218)]:
        cv2.circle(image, (x, y), 1, 40, -1)

    src = ROOT / "images" / "input" / f"scene_{name}.png"
    gt = ROOT / "images" / "reference" / f"scene_{name}_reference.png"
    src.parent.mkdir(parents=True, exist_ok=True)
    gt.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(src), np.clip(image, 0, 255).astype(np.uint8))
    cv2.imwrite(str(gt), reference)


def generate_diagonal_mask() -> None:
    """Pequenos quadrados em contato só pela diagonal mostram 4 versus 8."""
    mask = np.zeros((96, 120), dtype=np.uint8)
    mask[15:32, 15:32] = 255
    mask[32:49, 32:49] = 255   # liga só pela diagonal ao primeiro
    mask[22:44, 82:103] = 255  # terceiro componente isolado
    mask[68:71, 59:62] = 255   # ruído removível pela abertura
    cv2.imwrite(str(ROOT / "images" / "input" / "diagonal_demo_mask.png"), mask)


if __name__ == "__main__":
    generate("uniform", False)
    generate("uneven", True)
    generate_diagonal_mask()
    print("Imagens de exemplo e máscaras de referência criadas.")
