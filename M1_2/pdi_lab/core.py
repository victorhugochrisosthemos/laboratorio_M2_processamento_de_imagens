"""Operações de segmentação e análise de máscaras da M2."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import cv2
import numpy as np


class LabError(ValueError):
    """Erro de entrada, parâmetro ou saída com explicação para quem executa."""


def read_image(path: str | Path, *, binary_mask: bool = False) -> np.ndarray:
    file_path = Path(path)
    if not file_path.is_file():
        raise LabError(f"Arquivo não encontrado: {file_path}")
    image = cv2.imread(str(file_path), cv2.IMREAD_UNCHANGED)
    if image is None or image.size == 0:
        raise LabError(f"Não foi possível ler a imagem: {file_path}")
    if image.dtype != np.uint8:
        raise LabError("A imagem precisa ter 8 bits por canal (uint8).")
    if binary_mask:
        validate_mask(image)
        return image
    if image.ndim == 2:
        return image
    if image.ndim == 3 and image.shape[2] == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if image.ndim == 3 and image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    raise LabError("Formato de imagem incompatível: esperado cinza, BGR ou BGRA.")


def validate_mask(mask: np.ndarray) -> None:
    if not isinstance(mask, np.ndarray) or mask.ndim != 2 or mask.dtype != np.uint8:
        raise LabError("A máscara deve possuir um único canal e 8 bits.")
    if mask.size == 0 or not np.all((mask == 0) | (mask == 255)):
        raise LabError("Máscara não binária: somente 0 e 255 são aceitos.")


def segment(
    grayscale: np.ndarray,
    *,
    method: str = "fixed",
    threshold: int = 120,
    block_size: int = 75,
    c: float = 8.0,
    foreground: str = "dark",
) -> tuple[np.ndarray, dict]:
    if grayscale.ndim != 2 or grayscale.dtype != np.uint8 or grayscale.size == 0:
        raise LabError("A segmentação exige imagem em tons de cinza, uint8.")
    if method not in ("fixed", "adaptive", "otsu"):
        raise LabError("Método desconhecido: use fixed, adaptive ou otsu.")
    if foreground not in ("dark", "light"):
        raise LabError("Foreground inválido: escolha dark ou light.")
    if type(threshold) is not int or not 0 <= threshold <= 255:
        raise LabError("Limiar deve ser um número inteiro de 0 a 255.")
    if not isinstance(c, (int, float)) or not np.isfinite(c):
        raise LabError("O parâmetro C deve ser um número finito.")
    typ = cv2.THRESH_BINARY_INV if foreground == "dark" else cv2.THRESH_BINARY
    details = {"method": method, "foreground": foreground, "threshold": None,
               "block_size": None, "c": None}
    if method == "fixed":
        _, mask = cv2.threshold(grayscale, threshold, 255, typ)
        details["threshold"] = threshold
    elif method == "otsu":
        found, mask = cv2.threshold(grayscale, 0, 255, typ | cv2.THRESH_OTSU)
        details["threshold"] = round(float(found), 3)
    else:
        if type(block_size) is not int or block_size < 3 or block_size % 2 != 1:
            raise LabError("block-size deve ser ímpar e >= 3.")
        if block_size > min(grayscale.shape):
            raise LabError("block-size não pode ultrapassar a menor dimensão da imagem.")
        mask = cv2.adaptiveThreshold(
            grayscale, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            typ, block_size, float(c),
        )
        details["block_size"] = block_size
        details["c"] = float(c)
    validate_mask(mask)
    return mask, details


def component_stats(mask: np.ndarray, connectivity: int, min_area: int, stage: str):
    validate_mask(mask)
    if type(connectivity) is not int or connectivity not in (4, 8):
        raise LabError("connectivity deve ser 4 ou 8.")
    if type(min_area) is not int or min_area < 1:
        raise LabError("min-area deve ser inteiro e >= 1.")
    total, labels, stats, centroids = cv2.connectedComponentsWithStats(
        mask, connectivity=connectivity, ltype=cv2.CV_32S
    )
    rows = []
    for label in range(1, total):  # rótulo 0 é o fundo
        x, y, width, height, area = (int(v) for v in stats[label])
        rows.append({
            "stage": stage, "component_id": label, "area": area,
            "x": x, "y": y, "width": width, "height": height,
            "centroid_x": round(float(centroids[label][0]), 3),
            "centroid_y": round(float(centroids[label][1]), 3),
            "retained": area >= min_area,
        })
    assert sum(row["area"] for row in rows) == int(cv2.countNonZero(mask))
    return rows, labels


def apply_morphology(mask: np.ndarray, sequence: tuple[str, ...],
                     kernel_size: int, kernel_shape: str, iterations: int):
    validate_mask(mask)
    if not sequence or any(s not in ("open", "close") for s in sequence):
        raise LabError("sequence deve conter open e/ou close, separados por vírgula.")
    if type(kernel_size) is not int or kernel_size < 3 or kernel_size % 2 != 1:
        raise LabError("kernel-size deve ser ímpar e >= 3.")
    if kernel_size > min(mask.shape):
        raise LabError("kernel-size não pode exceder a menor dimensão da máscara.")
    if kernel_shape not in ("ellipse", "rect", "cross"):
        raise LabError("kernel-shape deve ser ellipse, rect ou cross.")
    if type(iterations) is not int or iterations < 1:
        raise LabError("iterations deve ser >= 1.")
    shapes = {"ellipse": cv2.MORPH_ELLIPSE, "rect": cv2.MORPH_RECT,
              "cross": cv2.MORPH_CROSS}
    kernel = cv2.getStructuringElement(shapes[kernel_shape], (kernel_size, kernel_size))
    current = mask.copy()
    steps = []
    for step_name in sequence:
        op = cv2.MORPH_OPEN if step_name == "open" else cv2.MORPH_CLOSE
        current = cv2.morphologyEx(current, op, kernel, iterations=iterations)
        validate_mask(current)
        steps.append((step_name, current.copy()))
    return steps


def _write_png(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), array):
        raise LabError(f"Falha ao gravar PNG: {path}")


def _write_json(path: Path, info: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(info, file, ensure_ascii=False, indent=2)
        file.write("\n")


def _write_csv(path: Path, rows: list[dict]) -> None:
    columns = ["stage", "component_id", "area", "x", "y", "width", "height",
               "centroid_x", "centroid_y", "retained"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _color_labels(mask: np.ndarray, rows: list[dict], labels: np.ndarray) -> np.ndarray:
    rendered = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    rendered[:, :] = (25, 25, 25)
    for row in rows:
        i = row["component_id"]
        color = (int(45 + i * 67 % 190), int(45 + i * 113 % 190),
                 int(45 + i * 41 % 190)) if row["retained"] else (90, 90, 90)
        rendered[labels == i] = color
        if row["retained"]:
            x, y, w, h = row["x"], row["y"], row["width"], row["height"]
            cv2.rectangle(rendered, (x, y), (x + w - 1, y + h - 1), (245, 245, 245), 1)
    return rendered


def _stage_summary(mask: np.ndarray, rows: list[dict]) -> dict:
    selected = [r for r in rows if r["retained"]]
    return {
        "foreground_pixels": int(cv2.countNonZero(mask)),
        "foreground_ratio": round(float(cv2.countNonZero(mask) / mask.size), 6),
        "raw_components": len(rows),
        "filtered_components": len(selected),
        "raw_area_sum": sum(r["area"] for r in rows),
        "filtered_area_sum": sum(r["area"] for r in selected),
    }


def run_segment(source: str, output: str, **kwargs) -> dict:
    in_path, out_path = Path(source), Path(output)
    if out_path.suffix.lower() != ".png":
        raise LabError("Saída de segmentação deve ser um arquivo .png.")
    if in_path.resolve() == out_path.resolve():
        raise LabError("A saída não pode substituir a imagem original.")
    gray = read_image(in_path)
    mask, params = segment(gray, **kwargs)
    info = {
        "operation": "segment", "input": str(in_path), "output": str(out_path),
        "width": int(gray.shape[1]), "height": int(gray.shape[0]),
        "mask_values": [0, 255], "foreground_pixels": int(cv2.countNonZero(mask)),
        "foreground_ratio": round(float(cv2.countNonZero(mask) / mask.size), 6),
        "parameters": params, "opencv_version": cv2.__version__,
    }
    _write_png(out_path, mask)
    _write_json(out_path.with_suffix(".json"), info)
    return info


def run_analyze(source: str, prefix: str, *, connectivity: int = 8,
                min_area: int = 20, sequence: tuple[str, ...] = ("open", "close"),
                kernel_size: int = 3, kernel_shape: str = "ellipse",
                iterations: int = 1) -> dict:
    mask = read_image(source, binary_mask=True)
    # Valida os parâmetros antes de escrever quaisquer arquivos.
    component_stats(mask, connectivity, min_area, "before")
    steps = apply_morphology(mask, sequence, kernel_size, kernel_shape, iterations)
    final_mask = steps[-1][1]
    before_rows, before_labels = component_stats(mask, connectivity, min_area, "before")
    after_rows, after_labels = component_stats(final_mask, connectivity, min_area, "after")
    out = Path(prefix)
    if not out.name:
        raise LabError("Informe um prefixo válido para os resultados.")
    if any((out.parent / (out.name + ending)).resolve() == Path(source).resolve()
           for ending in ("_before.png", "_after.png")):
        raise LabError("O prefixo não pode sobrescrever a máscara de entrada.")
    _write_png(Path(f"{out}_before.png"), mask)
    _write_png(Path(f"{out}_before_labels.png"), _color_labels(mask, before_rows, before_labels))
    for index, (name, intermediate) in enumerate(steps, 1):
        _write_png(Path(f"{out}_step_{index:02d}_{name}.png"), intermediate)
    _write_png(Path(f"{out}_after.png"), final_mask)
    _write_png(Path(f"{out}_after_labels.png"), _color_labels(final_mask, after_rows, after_labels))
    _write_csv(Path(f"{out}_before_components.csv"), before_rows)
    _write_csv(Path(f"{out}_after_components.csv"), after_rows)
    preview = np.hstack((cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR),
                         cv2.cvtColor(final_mask, cv2.COLOR_GRAY2BGR)))
    _write_png(Path(f"{out}_comparison.png"), preview)
    data = {
        "operation": "analyze", "input": str(source), "output_prefix": str(out),
        "width": mask.shape[1], "height": mask.shape[0],
        "parameters": {"connectivity": connectivity, "min_area": min_area,
                       "sequence": list(sequence), "kernel_size": kernel_size,
                       "kernel_shape": kernel_shape, "iterations": iterations},
        "before": _stage_summary(mask, before_rows),
        "after": _stage_summary(final_mask, after_rows),
        "changed_pixels": int(cv2.countNonZero(cv2.absdiff(mask, final_mask))),
        "intermediates": [f"{out}_step_{i:02d}_{name}.png"
                          for i, (name, _) in enumerate(steps, 1)],
        "opencv_version": cv2.__version__,
    }
    _write_json(Path(f"{out}_summary.json"), data)
    return data
