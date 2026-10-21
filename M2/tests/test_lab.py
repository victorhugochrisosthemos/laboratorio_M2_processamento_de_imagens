"""Testes controlados de segmentação, conectividade, morfologia e CLI."""
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import cv2
import numpy as np

from pdi_lab.core import (LabError, apply_morphology, component_stats,
                          read_image, run_analyze, run_segment, segment)


class SegmentTests(unittest.TestCase):
    def test_fixed_limiar_inclui_igual_para_objeto_escuro(self):
        image = np.array([[119, 120, 121, 255]], dtype=np.uint8)
        mask, meta = segment(image, method="fixed", threshold=120)
        np.testing.assert_array_equal(mask, [[255, 255, 0, 0]])
        self.assertEqual(meta["threshold"], 120)

    def test_foreground_claro(self):
        image = np.array([[50, 120, 220]], dtype=np.uint8)
        mask, _ = segment(image, method="fixed", threshold=120, foreground="light")
        np.testing.assert_array_equal(mask, [[0, 0, 255]])

    def test_adaptive_e_otsu_saidas_binarias(self):
        image = np.tile(np.arange(80, 160, dtype=np.uint8), (80, 1))
        for method in ("adaptive", "otsu"):
            mask, _ = segment(image, method=method, block_size=15)
            self.assertEqual(mask.shape, image.shape)
            self.assertTrue(set(np.unique(mask)).issubset({0, 255}))

    def test_parametros_invalidos(self):
        image = np.full((15, 15), 150, np.uint8)
        for params in ({"method": "nope"}, {"threshold": -1},
                       {"method": "adaptive", "block_size": 4},
                       {"method": "adaptive", "block_size": 17},
                       {"foreground": "green"}, {"method": "adaptive", "c": float("nan")}):
            with self.subTest(params=params), self.assertRaises(LabError):
                segment(image, **params)


class ComponentTests(unittest.TestCase):
    def test_conectividade_diagonal(self):
        mask = np.zeros((8, 8), np.uint8)
        mask[1:3, 1:3] = 255
        mask[3:5, 3:5] = 255
        rows4, _ = component_stats(mask, 4, 1, "before")
        rows8, _ = component_stats(mask, 8, 1, "before")
        self.assertEqual([r["area"] for r in rows4], [4, 4])
        self.assertEqual([r["area"] for r in rows8], [8])

    def test_exatamente_dois_pixels_na_diagonal(self):
        mask = np.zeros((5, 5), np.uint8)
        mask[1, 1] = 255
        mask[2, 2] = 255
        for connectivity, expected in ((4, 2), (8, 1)):
            rows, _ = component_stats(mask, connectivity, 0, "before")
            self.assertEqual(len(rows), expected)
            self.assertEqual(sum(r["area"] for r in rows), 2)

    def test_mascara_vazia_e_objeto_na_borda(self):
        empty = np.zeros((10, 10), np.uint8)
        rows, _ = component_stats(empty, 4, 1, "before")
        self.assertEqual(rows, [])
        mask = empty.copy()
        mask[0:2, 0:3] = 255
        rows, _ = component_stats(mask, 8, 1, "before")
        self.assertEqual(rows[0]["area"], 6)
        self.assertEqual((rows[0]["x"], rows[0]["y"]), (0, 0))
        self.assertEqual((rows[0]["width"], rows[0]["height"]), (3, 2))
        self.assertAlmostEqual(rows[0]["cx"], 1.0)
        self.assertAlmostEqual(rows[0]["cy"], 0.5)

    def test_abertura_remove_ruido(self):
        mask = np.zeros((25, 25), np.uint8)
        mask[4:16, 4:16] = 255
        mask[20, 20] = 255
        result = apply_morphology(mask, ("open", "close"), 3, "ellipse", 1)[-1][1]
        self.assertEqual(result[20, 20], 0)
        self.assertEqual(result[9, 9], 255)

    def test_mascara_invalida(self):
        with self.assertRaisesRegex(LabError, "não binária"):
            component_stats(np.array([[0, 128, 255]], np.uint8), 4, 1, "before")
        with self.assertRaisesRegex(LabError, "único canal"):
            component_stats(np.zeros((3, 3, 3), np.uint8), 4, 1, "before")

    def test_filtro_preserva_contagem_bruta(self):
        mask = np.zeros((30, 30), np.uint8)
        mask[1:5, 1:5] = 255
        mask[15, 15] = 255
        rows, _ = component_stats(mask, 8, 5, "before")
        self.assertEqual(len(rows), 2)
        self.assertEqual(sum(r["kept"] for r in rows), 1)


    def test_min_area_zero_e_filtragem(self):
        mask = np.zeros((8, 8), dtype=np.uint8)
        mask[2, 2] = 255
        rows, _ = component_stats(mask, 4, 0, "before")
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["kept"])

    def test_fechamento_preenche_furo_pequeno(self):
        mask = np.zeros((20, 20), dtype=np.uint8)
        mask[3:17, 3:17] = 255
        mask[10, 10] = 0
        steps = apply_morphology(mask, ("close", "open"), 3, "rect", 1)
        self.assertEqual(steps[0][1][10, 10], 255)

    def test_args_invalidos(self):
        mask = np.zeros((8, 8), np.uint8)
        for conn, area in ((5, 1), (8, -1), (4, -1)):
            with self.assertRaises(LabError):
                component_stats(mask, conn, area, "before")
        for seq, k, shape, iterations in (((), 3, "ellipse", 1),
                                          (("open",), 3, "ellipse", 1),
                                          (("open", "open"), 3, "ellipse", 1),
                                          (("dilate", "close"), 3, "ellipse", 1),
                                          (("open", "close"), 2, "ellipse", 1),
                                          (("open", "close"), 3, "triangle", 1),
                                          (("open", "close"), 3, "ellipse", 0)):
            with self.assertRaises(LabError):
                apply_morphology(mask, seq, k, shape, iterations)


class FilesAndCLITests(unittest.TestCase):
    def test_exportacao_medidas_e_reexecucao(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            original = np.full((40, 40), 235, np.uint8)
            cv2.rectangle(original, (8, 8), (20, 20), 50, -1)
            input_file = directory / "original.png"
            cv2.imwrite(str(input_file), original)
            mask_file = directory / "mask.png"
            run_segment(str(input_file), str(mask_file), method="fixed", threshold=100)
            mask = read_image(mask_file, binary_mask=True)
            self.assertEqual(mask.ndim, 2)
            prefix = str(directory / "subdir" / "analysis")
            first = run_analyze(str(mask_file), prefix, connectivity=8, min_area=10)
            second = run_analyze(str(mask_file), prefix, connectivity=8, min_area=10)
            self.assertEqual(first, second)
            self.assertEqual(first["before"]["raw_components"], 1)

            csv_file = Path(prefix + "_before_components.csv")
            with csv_file.open(encoding="utf-8", newline="") as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(list(rows[0].keys()), ["label", "area", "x", "y", "width", "height", "cx", "cy", "kept"])
            self.assertEqual(int(rows[0]["area"]), 169)
            self.assertEqual(first["before"]["raw_area_sum"],
                             first["before"]["foreground_pixels"])
            self.assertEqual(first["after"]["raw_area_sum"],
                             first["after"]["foreground_pixels"])
            self.assertTrue(Path(prefix + "_summary.json").is_file())

    def test_arquivo_inexistente_e_nao_binario(self):
        with tempfile.TemporaryDirectory() as temp:
            prefix = Path(temp) / "teste"
            with self.assertRaises(LabError):
                run_analyze("nao_existe.png", str(prefix))
            path = Path(temp) / "gray.png"
            cv2.imwrite(str(path), np.full((20, 20), 128, np.uint8))
            with self.assertRaises(LabError):
                run_analyze(str(path), str(prefix))


    def test_duas_fotografias_em_duas_configuracoes_e_conectividades(self):
        root = Path(__file__).resolve().parents[1]
        photos = (("foto_moedas.png", 120), ("foto_xicara.png", 170))
        with tempfile.TemporaryDirectory() as temp:
            for filename, threshold in photos:
                image_path = root / "images" / "input" / filename
                original = read_image(image_path)
                self.assertGreater(original.size, 0)
                for method in ("fixed", "adaptive"):
                    output = Path(temp) / (filename.replace(".png", "") + "_" + method + ".png")
                    params = {"method": method, "foreground": "light"}
                    if method == "fixed":
                        params["threshold"] = threshold
                    else:
                        params.update({"block_size": 75, "c": -4})
                    run_segment(str(image_path), str(output), **params)
                    mask = read_image(output, binary_mask=True)
                    self.assertEqual(mask.shape, original.shape)
                    self.assertTrue(set(np.unique(mask)).issubset({0, 255}))
                    for conn in (4, 8):
                        result = run_analyze(str(output), str(Path(temp) / f"analysis_{conn}"),
                                             connectivity=conn, min_area=20)
                        self.assertEqual(result["before"]["raw_area_sum"],
                                         result["before"]["foreground_pixels"])
                        self.assertEqual(result["after"]["raw_area_sum"],
                                         result["after"]["foreground_pixels"])

    def test_cli_codigo_de_saida(self):
        root = Path(__file__).resolve().parents[1]
        cmd = [sys.executable, "-m", "pdi_lab", "--operation", "segment",
               "--input", "nao_existe.png", "--output", "foo.png"]
        process = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("Arquivo não encontrado", process.stderr)
        help_run = subprocess.run([sys.executable, "-m", "pdi_lab", "--help"],
                                  cwd=root, capture_output=True, text=True)
        self.assertEqual(help_run.returncode, 0)
        self.assertIn("--connectivity", help_run.stdout)


if __name__ == "__main__":
    unittest.main()
