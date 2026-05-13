from __future__ import annotations

import csv
import json
import random
import statistics as stats
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


class ADCReader(Protocol):
    """Minimal interface for ADC implementations."""

    def read(self, channel: int = 0) -> int:
        """Return one raw ADC value."""


class SimulatedADC:
    """Small noisy ADC simulator for development without Raspberry Pi hardware."""

    def __init__(self, center: int = 512, noise: int = 12) -> None:
        self.center = center
        self.noise = noise

    def read(self, channel: int = 0) -> int:
        del channel
        return max(0, min(1023, int(random.gauss(self.center, self.noise))))


@dataclass(frozen=True)
class Measurement:
    index: int
    timestamp: float
    channel: int
    raw_average: float
    calibrated_value: float
    samples: tuple[int, ...]


@dataclass
class MeasurementSession:
    adc: ADCReader
    channel: int = 0
    samples_per_measurement: int = 35
    sample_delay_seconds: float = 0.01
    calibration_factor: float = 1.0
    measurements: list[Measurement] = field(default_factory=list)

    def measure(self) -> Measurement:
        samples = self._read_samples()
        raw_average = stats.mean(samples)
        measurement = Measurement(
            index=len(self.measurements) + 1,
            timestamp=time.time(),
            channel=self.channel,
            raw_average=raw_average,
            calibrated_value=raw_average * self.calibration_factor,
            samples=tuple(samples),
        )
        self.measurements.append(measurement)
        return measurement

    def measure_many(self, count: int) -> list[Measurement]:
        if count < 1:
            raise ValueError("El numero de mediciones debe ser mayor que cero.")
        return [self.measure() for _ in range(count)]

    def calibrate(self, known_value: float, readings: int = 29) -> float:
        if known_value <= 0:
            raise ValueError("El valor de calibracion debe ser mayor que cero.")
        if readings < 1:
            raise ValueError("La calibracion necesita al menos una lectura.")

        raw_values = [stats.mean(self._read_samples()) for _ in range(readings)]
        raw_average = stats.mean(raw_values)
        if raw_average == 0:
            raise ValueError("No se puede calibrar con lectura cruda igual a cero.")

        self.calibration_factor = known_value / raw_average
        return self.calibration_factor

    def reset(self) -> None:
        self.measurements.clear()

    def values(self) -> list[float]:
        return [measurement.calibrated_value for measurement in self.measurements]

    def summary(self) -> dict[str, float | int]:
        values = self.values()
        if not values:
            return {
                "count": 0,
                "min": 0.0,
                "max": 0.0,
                "mean": 0.0,
                "std_dev": 0.0,
            }

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": stats.mean(values),
            "std_dev": stats.pstdev(values) if len(values) > 1 else 0.0,
        }

    def _read_samples(self) -> list[int]:
        samples: list[int] = []
        for _ in range(self.samples_per_measurement):
            samples.append(self.adc.read(self.channel))
            if self.sample_delay_seconds:
                time.sleep(self.sample_delay_seconds)
        return samples


def export_csv(path: str | Path, measurements: list[Measurement]) -> Path:
    output_path = Path(path)
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            [
                "index",
                "timestamp",
                "channel",
                "raw_average",
                "calibrated_value",
                "samples",
            ]
        )
        for measurement in measurements:
            writer.writerow(
                [
                    measurement.index,
                    time.strftime(
                        "%Y-%m-%d %H:%M:%S",
                        time.localtime(measurement.timestamp),
                    ),
                    measurement.channel,
                    f"{measurement.raw_average:.6f}",
                    f"{measurement.calibrated_value:.6f}",
                    " ".join(str(sample) for sample in measurement.samples),
                ]
            )
    return output_path


def export_json(path: str | Path, measurements: list[Measurement]) -> Path:
    output_path = Path(path)
    payload = [
        {
            "index": measurement.index,
            "timestamp": measurement.timestamp,
            "channel": measurement.channel,
            "raw_average": measurement.raw_average,
            "calibrated_value": measurement.calibrated_value,
            "samples": list(measurement.samples),
        }
        for measurement in measurements
    ]
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path

