"""Entry point: python -m generator --seed 15037 --out data/raw (dijalankan dari folder ml/)."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from generator import config
from generator.pipeline import run, write
from generator.validate import print_summary, validate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m generator", description="Generator data sintetis ProcureWise")
    parser.add_argument("--seed", type=int, default=config.DEFAULT_SEED,
                        help=f"seed utama (default {config.DEFAULT_SEED})")
    parser.add_argument("--out", type=Path, default=config.DEFAULT_OUT_DIR,
                        help="folder output CSV (default ml/data/raw)")
    args = parser.parse_args(argv)

    started = time.perf_counter()
    print(f"Generate data sintetis dengan seed {args.seed} ke {args.out.resolve()}")
    data = run(args.seed)
    manifest = write(data, args.out, args.seed)
    print(f"Selesai dalam {time.perf_counter() - started:.1f} detik")

    report, tables = validate(args.out)
    print_summary(report, tables, manifest)
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
