"""Interface de linha de comando: python -m pdi_lab --help."""

import argparse
import sys

import cv2

from .core import LabError, run_analyze, run_segment


def create_parser():
    parser = argparse.ArgumentParser(
        prog="python -m pdi_lab",
        description="M2: segmentação de imagens e análise de componentes de máscaras.",
    )
    parser.add_argument("--operation", required=True, choices=["segment", "analyze"])
    parser.add_argument("--input", required=True, help="Imagem para segment, máscara PNG para analyze")
    parser.add_argument("--output", required=True,
                        help="Arquivo .png para segment, prefixo de arquivos para analyze")
    group1 = parser.add_argument_group("Segmentação (M2.1)")
    group1.add_argument("--method", default="fixed", choices=["fixed", "adaptive", "otsu"])
    group1.add_argument("--foreground", default="dark", choices=["dark", "light"])
    group1.add_argument("--threshold", type=int, default=120)
    group1.add_argument("--block-size", type=int, default=75)
    group1.add_argument("--c", type=float, default=8.0)
    group2 = parser.add_argument_group("Componentes e morfologia (M2.2)")
    group2.add_argument("--connectivity", type=int, default=8)
    group2.add_argument("--min-area", type=int, default=20)
    group2.add_argument("--sequence", default="open,close", help="Por exemplo: open,close ou close,open")
    group2.add_argument("--kernel-size", type=int, default=3)
    group2.add_argument("--kernel-shape", default="ellipse", choices=["ellipse", "rect", "cross"])
    group2.add_argument("--iterations", type=int, default=1)
    return parser


def main(argv=None) -> int:
    args = create_parser().parse_args(argv)
    try:
        if args.operation == "segment":
            data = run_segment(
                args.input, args.output, method=args.method,
                foreground=args.foreground, threshold=args.threshold,
                block_size=args.block_size, c=args.c,
            )
            print(f"OK: {data['foreground_pixels']} pixels de objeto; máscara: {data['output']}")
        else:
            if args.sequence.strip() == "":
                raise LabError("Informe uma sequência morfológica, como open,close.")
            sequence = tuple(s.strip() for s in args.sequence.split(","))
            data = run_analyze(
                args.input, args.output, connectivity=args.connectivity,
                min_area=args.min_area, sequence=sequence,
                kernel_size=args.kernel_size, kernel_shape=args.kernel_shape,
                iterations=args.iterations,
            )
            print("OK: componentes brutos antes/depois: "
                  f"{data['before']['raw_components']}/{data['after']['raw_components']}; "
                  f"resumo: {data['output_prefix']}_summary.json")
    except (LabError, OSError, cv2.error) as err:
        print(f"Erro: {err}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
