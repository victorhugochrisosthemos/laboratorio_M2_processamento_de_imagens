"""Executa as duas etapas e recria todos os resultados do projeto.

Execute na raiz M1_2: python tools/reproduce.py
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def run(*arguments: str) -> str:
    command = [sys.executable, "-m", "pdi_lab", *arguments]
    process = subprocess.run(command, cwd=ROOT, text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode != 0:
        raise RuntimeError(f"Falha em {' '.join(command)}\n{process.stderr}")
    return process.stdout.strip()


def error_image(reference: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, dict]:
    """Vermelho: incluído por engano; azul: objeto perdido; branco: acerto."""
    fp = (mask == 255) & (reference == 0)
    fn = (mask == 0) & (reference == 255)
    rgb = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    rgb[fp] = (20, 20, 255)
    rgb[fn] = (255, 70, 30)
    metrics = {"false_positive_pixels": int(np.count_nonzero(fp)),
               "false_negative_pixels": int(np.count_nonzero(fn)),
               "total_errors": int(np.count_nonzero(fp) + np.count_nonzero(fn))}
    return rgb, metrics


def main() -> None:
    # Não modifica os arquivos-fonte; apenas recria entradas e resultados.
    from generate_inputs import generate, generate_diagonal_mask
    generate("uniform", False)
    generate("uneven", True)
    generate_diagonal_mask()
    log = []
    evaluation = {}
    for scene in ("uniform", "uneven"):
        original = f"images/input/scene_{scene}.png"
        truth = cv2.imread(str(ROOT / "images" / "reference" /
                                    f"scene_{scene}_reference.png"), cv2.IMREAD_GRAYSCALE)
        metrics = {}
        error_panels = []
        for method in ("fixed", "adaptive"):
            output = f"images/output/scene_{scene}_{method}.png"
            method_args = (["--threshold", "120"] if method == "fixed"
                           else ["--block-size", "75", "--c", "8"])
            log.append(run("--operation", "segment", "--input", original,
                           "--output", output, "--method", method,
                           "--foreground", "dark", *method_args))
            mask = cv2.imread(str(ROOT / output), cv2.IMREAD_GRAYSCALE)
            panel, metrics[method] = error_image(truth, mask)
            error_panels.append(panel)
        comparison = np.hstack(error_panels)  # esquerda fixo, direita adaptativo
        titlebar = np.full((42, comparison.shape[1], 3), 245, dtype=np.uint8)
        cv2.putText(titlebar, "Fixo: inclusao vermelha / exclusao azul", (8, 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (20, 20, 20), 1)
        cv2.putText(titlebar, "Adaptativo: inclusao vermelha / exclusao azul",
                    (comparison.shape[1] // 2 + 8, 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (20, 20, 20), 1)
        comparison = np.vstack((titlebar, comparison))
        cv2.imwrite(str(ROOT / "images" / "output" /
                        f"scene_{scene}_errors.png"), comparison)
        evaluation[scene] = metrics
        chosen = f"images/output/scene_{scene}_adaptive.png"
        for connectivity in (4, 8):
            prefix = f"results/scene_{scene}_c{connectivity}"
            log.append(run("--operation", "analyze", "--input", chosen,
                           "--output", prefix, "--connectivity", str(connectivity),
                           "--min-area", "20", "--sequence", "open,close",
                           "--kernel-size", "3", "--kernel-shape", "ellipse",
                           "--iterations", "1"))
    for connectivity in (4, 8):
        log.append(run("--operation", "analyze", "--input",
                       "images/input/diagonal_demo_mask.png", "--output",
                       f"results/diagonal_c{connectivity}", "--connectivity",
                       str(connectivity), "--min-area", "20", "--sequence",
                       "open,close", "--kernel-size", "3"))
    (ROOT / "results" / "reproduction_log.txt").write_text(
        "\n".join(log) + "\n", encoding="utf-8")
    (ROOT / "results" / "segmentation_evaluation.json").write_text(
        json.dumps(evaluation, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print("Resultados reproduzidos. Veja results/ e images/output/.")


if __name__ == "__main__":
    main()
