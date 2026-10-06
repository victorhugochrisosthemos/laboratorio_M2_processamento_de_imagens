from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np

LOSSLESS_EXTENSIONS = {".png", ".bmp", ".tif", ".tiff"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdi_lab",
        description="Segmentação binária para o laboratório M2.1.",
    )
    parser.add_argument("--input", required=True, help="Imagem de entrada.")
    parser.add_argument("--output", required=True, help="Máscara de saída (formato sem perdas).")
    parser.add_argument("--operation", required=True, choices=["segment"])
    parser.add_argument(
        "--method",
        required=True,
        choices=["fixed", "otsu", "adaptive", "hsv"],
    )

    parser.add_argument("--threshold", type=int, default=115, help="Limiar fixo [0,255].")
    parser.add_argument(
        "--invert",
        action="store_true",
        help="Marca como objeto os pixels mais escuros que o limiar.",
    )
    parser.add_argument(
        "--blur-ksize",
        type=int,
        default=0,
        help="Kernel gaussiano: 0 desativa; caso contrário use ímpar >= 3.",
    )

    parser.add_argument("--block-size", type=int, default=31, help="Janela do limiar adaptativo.")
    parser.add_argument("--c", type=float, default=8.0, help="Constante C do limiar adaptativo.")

    parser.add_argument("--h-min", type=int, default=0)
    parser.add_argument("--h-max", type=int, default=179)
    parser.add_argument("--s-min", type=int, default=0)
    parser.add_argument("--s-max", type=int, default=255)
    parser.add_argument("--v-min", type=int, default=0)
    parser.add_argument("--v-max", type=int, default=255)

    parser.add_argument(
        "--overlay",
        help="Opcional: salva uma visualização da máscara sobre a imagem original.",
    )
    parser.add_argument(
        "--stats-json",
        help="Opcional: salva dimensões e proporção de primeiro plano em JSON.",
    )
    return parser


def _validate_blur_ksize(value: int) -> None:
    if value != 0 and (value < 3 or value % 2 == 0):
        raise ValueError("--blur-ksize deve ser 0 ou um número ímpar >= 3")


def _validate_args(args: argparse.Namespace) -> None:
    if not 0 <= args.threshold <= 255:
        raise ValueError("--threshold deve estar entre 0 e 255")
    _validate_blur_ksize(args.blur_ksize)

    if args.block_size < 3 or args.block_size % 2 == 0:
        raise ValueError("--block-size deve ser ímpar e >= 3")

    for name, value, upper in (
        ("h-min", args.h_min, 179),
        ("h-max", args.h_max, 179),
        ("s-min", args.s_min, 255),
        ("s-max", args.s_max, 255),
        ("v-min", args.v_min, 255),
        ("v-max", args.v_max, 255),
    ):
        if not 0 <= value <= upper:
            raise ValueError(f"--{name} deve estar entre 0 e {upper}")

    if args.s_min > args.s_max:
        raise ValueError("--s-min não pode ser maior que --s-max")
    if args.v_min > args.v_max:
        raise ValueError("--v-min não pode ser maior que --v-max")

    output_ext = Path(args.output).suffix.lower()
    if output_ext not in LOSSLESS_EXTENSIONS:
        raise ValueError("a máscara deve ser salva em PNG, BMP ou TIFF; JPEG não é aceito")

    if args.overlay:
        overlay_ext = Path(args.overlay).suffix.lower()
        if overlay_ext not in LOSSLESS_EXTENSIONS:
            raise ValueError("a sobreposição deve usar um formato sem perdas")


def read_image(path: str | Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"não foi possível ler a imagem: {path}")
    return image


def _blur(image: np.ndarray, ksize: int) -> np.ndarray:
    if ksize == 0:
        return image
    return cv2.GaussianBlur(image, (ksize, ksize), 0)


def _gray(image: np.ndarray, blur_ksize: int) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return _blur(gray, blur_ksize)


def _threshold_type(invert: bool) -> int:
    return cv2.THRESH_BINARY_INV if invert else cv2.THRESH_BINARY


def segment_array(
    image: np.ndarray,
    *,
    method: str,
    threshold: int = 115,
    invert: bool = False,
    blur_ksize: int = 0,
    block_size: int = 31,
    c: float = 8.0,
    h_min: int = 0,
    h_max: int = 179,
    s_min: int = 0,
    s_max: int = 255,
    v_min: int = 0,
    v_max: int = 255,
) -> np.ndarray:
    """Retorna uma máscara uint8, canal único, contendo apenas 0 e 255."""
    _validate_blur_ksize(blur_ksize)

    if method == "fixed":
        if not 0 <= threshold <= 255:
            raise ValueError("threshold fora do intervalo [0,255]")
        gray = _gray(image, blur_ksize)
        _, mask = cv2.threshold(gray, threshold, 255, _threshold_type(invert))

    elif method == "otsu":
        gray = _gray(image, blur_ksize)
        threshold_flag = _threshold_type(invert) | cv2.THRESH_OTSU
        _, mask = cv2.threshold(gray, 0, 255, threshold_flag)

    elif method == "adaptive":
        if block_size < 3 or block_size % 2 == 0:
            raise ValueError("block_size deve ser ímpar e >= 3")
        gray = _gray(image, blur_ksize)
        mask = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            _threshold_type(invert),
            block_size,
            c,
        )

    elif method == "hsv":
        for value, upper, label in (
            (h_min, 179, "h_min"),
            (h_max, 179, "h_max"),
            (s_min, 255, "s_min"),
            (s_max, 255, "s_max"),
            (v_min, 255, "v_min"),
            (v_max, 255, "v_max"),
        ):
            if not 0 <= value <= upper:
                raise ValueError(f"{label} fora do intervalo")
        if s_min > s_max or v_min > v_max:
            raise ValueError("intervalo HSV inválido")

        preprocessed = _blur(image, blur_ksize)
        hsv = cv2.cvtColor(preprocessed, cv2.COLOR_BGR2HSV)
        lower_sv = np.array([0, s_min, v_min], dtype=np.uint8)
        upper_sv = np.array([0, s_max, v_max], dtype=np.uint8)

        if h_min <= h_max:
            lower_sv[0] = h_min
            upper_sv[0] = h_max
            mask = cv2.inRange(hsv, lower_sv, upper_sv)
        else:
            # Matiz do OpenCV vai de 0 a 179. Quando h_min > h_max,
            # a faixa cruza a descontinuidade e é dividida em duas partes.
            low_a = np.array([h_min, s_min, v_min], dtype=np.uint8)
            high_a = np.array([179, s_max, v_max], dtype=np.uint8)
            low_b = np.array([0, s_min, v_min], dtype=np.uint8)
            high_b = np.array([h_max, s_max, v_max], dtype=np.uint8)
            mask = cv2.bitwise_or(
                cv2.inRange(hsv, low_a, high_a),
                cv2.inRange(hsv, low_b, high_b),
            )

        if invert:
            mask = cv2.bitwise_not(mask)
    else:
        raise ValueError(f"método desconhecido: {method}")

    if mask.dtype != np.uint8:
        mask = mask.astype(np.uint8)
    mask = np.where(mask > 0, 255, 0).astype(np.uint8)
    return mask


def validate_mask(mask: np.ndarray, expected_shape: tuple[int, int]) -> None:
    if mask.ndim != 2:
        raise ValueError("a máscara final deve ter um único canal")
    if mask.shape != expected_shape:
        raise ValueError("a máscara final não preservou largura e altura")
    values = set(int(v) for v in np.unique(mask))
    if not values.issubset({0, 255}):
        raise ValueError(f"a máscara não é binária: valores encontrados {sorted(values)}")


def foreground_stats(mask: np.ndarray) -> dict[str, int | float | bool | list[int]]:
    unique = [int(v) for v in np.unique(mask)]
    foreground_pixels = int(np.count_nonzero(mask == 255))
    total_pixels = int(mask.size)
    return {
        "width": int(mask.shape[1]),
        "height": int(mask.shape[0]),
        "channels": 1,
        "foreground_pixels": foreground_pixels,
        "total_pixels": total_pixels,
        "foreground_ratio": foreground_pixels / total_pixels,
        "values": unique,
        "binary": set(unique).issubset({0, 255}),
    }


def make_overlay(image: np.ndarray, mask: np.ndarray) -> np.ndarray:
    tint = image.copy()
    tint[mask == 255] = (0, 0, 255)
    return cv2.addWeighted(image, 0.67, tint, 0.33, 0)


def _write_image(path: str | Path, image: np.ndarray) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(destination), image):
        raise OSError(f"não foi possível salvar: {destination}")


def run(args: argparse.Namespace) -> int:
    try:
        _validate_args(args)
        image = read_image(args.input)
        mask = segment_array(
            image,
            method=args.method,
            threshold=args.threshold,
            invert=args.invert,
            blur_ksize=args.blur_ksize,
            block_size=args.block_size,
            c=args.c,
            h_min=args.h_min,
            h_max=args.h_max,
            s_min=args.s_min,
            s_max=args.s_max,
            v_min=args.v_min,
            v_max=args.v_max,
        )
        validate_mask(mask, image.shape[:2])
        _write_image(args.output, mask)

        if args.overlay:
            _write_image(args.overlay, make_overlay(image, mask))

        stats = foreground_stats(mask)
        if args.stats_json:
            stats_path = Path(args.stats_json)
            stats_path.parent.mkdir(parents=True, exist_ok=True)
            stats_path.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")

        print(
            f"method={args.method} "
            f"foreground_pixels={stats['foreground_pixels']} "
            f"foreground_ratio={stats['foreground_ratio']:.6f} "
            f"binary={stats['binary']} "
            f"output={args.output}"
        )
        return 0
    except (ValueError, OSError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
