from __future__ import annotations

import argparse
from pathlib import Path

from medidor.core import MeasurementSession, export_csv, export_json
from medidor.hardware import create_adc


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mediciones sin interfaz grafica")
    parser.add_argument("--count", type=int, default=1, help="numero de mediciones")
    parser.add_argument("--channel", type=int, default=0, help="canal MCP3008")
    parser.add_argument("--samples", type=int, default=35, help="muestras por medicion")
    parser.add_argument("--delay", type=float, default=0.01, help="pausa entre muestras")
    parser.add_argument("--calibration-factor", type=float, default=1.0)
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--json", type=Path)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    session = MeasurementSession(
        adc=create_adc(simulate=args.simulate),
        channel=args.channel,
        samples_per_measurement=args.samples,
        sample_delay_seconds=args.delay,
        calibration_factor=args.calibration_factor,
    )
    session.measure_many(args.count)
    summary = session.summary()
    print(
        "Mediciones: {count} | promedio: {mean:.3f} | min: {min:.3f} | "
        "max: {max:.3f} | desv: {std_dev:.3f}".format(**summary)
    )
    if args.csv:
        export_csv(args.csv, session.measurements)
    if args.json:
        export_json(args.json, session.measurements)


if __name__ == "__main__":
    main()

