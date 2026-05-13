from __future__ import annotations

import csv
import json
import unittest

from medidor.core import MeasurementSession, export_csv, export_json


class FixedADC:
    def __init__(self, values: list[int]) -> None:
        self.values = values
        self.index = 0

    def read(self, channel: int = 0) -> int:
        del channel
        value = self.values[self.index % len(self.values)]
        self.index += 1
        return value


class CoreTests(unittest.TestCase):
    def test_measure_stores_one_averaged_measurement(self) -> None:
        session = MeasurementSession(
            adc=FixedADC([10, 20, 30]),
            samples_per_measurement=3,
            sample_delay_seconds=0,
        )

        measurement = session.measure()

        self.assertEqual(measurement.raw_average, 20)
        self.assertEqual(measurement.calibrated_value, 20)
        self.assertEqual(measurement.samples, (10, 20, 30))
        self.assertEqual(session.values(), [20])

    def test_measurements_do_not_reuse_previous_samples(self) -> None:
        session = MeasurementSession(
            adc=FixedADC([10, 20, 30, 100, 110, 120]),
            samples_per_measurement=3,
            sample_delay_seconds=0,
        )

        first = session.measure()
        second = session.measure()

        self.assertEqual(first.raw_average, 20)
        self.assertEqual(second.raw_average, 110)
        self.assertEqual(session.values(), [20, 110])

    def test_calibration_updates_factor(self) -> None:
        session = MeasurementSession(
            adc=FixedADC([50]),
            samples_per_measurement=2,
            sample_delay_seconds=0,
        )

        factor = session.calibrate(known_value=100, readings=2)
        measurement = session.measure()

        self.assertEqual(factor, 2)
        self.assertEqual(measurement.calibrated_value, 100)

    def test_calibration_rejects_invalid_known_value(self) -> None:
        session = MeasurementSession(
            adc=FixedADC([50]),
            samples_per_measurement=1,
            sample_delay_seconds=0,
        )

        with self.assertRaises(ValueError):
            session.calibrate(known_value=0)

    def test_export_csv_and_json(self) -> None:
        with self.subTest("exports"):
            import tempfile
            from pathlib import Path

            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
                session = MeasurementSession(
                    adc=FixedADC([10, 20]),
                    samples_per_measurement=2,
                    sample_delay_seconds=0,
                )
                session.measure()

                csv_path = export_csv(tmp_path / "measurements.csv", session.measurements)
                json_path = export_json(
                    tmp_path / "measurements.json",
                    session.measurements,
                )

                with csv_path.open(newline="", encoding="utf-8") as csv_file:
                    rows = list(csv.DictReader(csv_file))
                payload = json.loads(json_path.read_text(encoding="utf-8"))

                self.assertEqual(rows[0]["raw_average"], "15.000000")
                self.assertEqual(payload[0]["samples"], [10, 20])


if __name__ == "__main__":
    unittest.main()
