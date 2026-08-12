import csv
from pathlib import Path

import pytest

from medidor.core import Calibration, MeasurementSession, export_csv


class ADC:
    def __init__(self, values): self.values=iter(values)
    def read(self, channel=0): return next(self.values)


def test_two_point_calibration():
    c=Calibration.from_two_points(100,0,500,1000)
    assert c.offset == 100
    assert c.slope == 2.5
    assert c.apply(300) == 500


@pytest.mark.parametrize("channel",[-1,8])
def test_invalid_channel(channel):
    with pytest.raises(ValueError): MeasurementSession(ADC([1]),channel=channel)


def test_rejects_adc_outside_range():
    session=MeasurementSession(ADC([1024]),samples_per_measurement=1,sample_delay_seconds=0)
    with pytest.raises(ValueError): session.measure()


def test_export_contains_traceability(tmp_path: Path):
    session=MeasurementSession(ADC([10,20]),samples_per_measurement=2,sample_delay_seconds=0,sensor_id="beam-a")
    session.measure(); path=export_csv(tmp_path/"data.csv",session.measurements)
    row=next(csv.DictReader(path.open(encoding="utf-8")))
    assert row["sensor_id"] == "beam-a"
    assert row["timestamp_iso"].endswith("+00:00")
    assert row["raw_std_dev"] == "5.000000"
