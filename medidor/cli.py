from __future__ import annotations

import argparse
from medidor.core import MeasurementSession, export_csv, export_json
from medidor.hardware import create_adc


def main() -> None:
    p=argparse.ArgumentParser(description="MCP3008 strain measurement CLI"); p.add_argument("--simulate",action="store_true"); p.add_argument("--count",type=int,default=1); p.add_argument("--channel",type=int,default=0); p.add_argument("--samples",type=int,default=35); p.add_argument("--delay",type=float,default=.01); p.add_argument("--factor",type=float,default=1); p.add_argument("--offset",type=float,default=0); p.add_argument("--unit",default="µε"); p.add_argument("--sensor",default="sensor-1"); p.add_argument("--csv"); p.add_argument("--json"); a=p.parse_args()
    s=MeasurementSession(create_adc(a.simulate),a.channel,a.samples,a.delay,a.factor,a.offset,a.unit,a.sensor); s.measure_many(a.count)
    for m in s.measurements: print(f"{m.timestamp_iso} {m.sensor_id} ADC={m.raw_average:.3f} value={m.calibrated_value:.3f} {m.unit}")
    if a.csv: export_csv(a.csv,s.measurements)
    if a.json: export_json(a.json,s.measurements)


if __name__=="__main__":main()
