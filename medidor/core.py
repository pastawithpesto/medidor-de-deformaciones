from __future__ import annotations

import csv
import json
import random
import statistics as stats
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol


class ADCReader(Protocol):
    def read(self, channel: int = 0) -> int: ...


class SimulatedADC:
    def __init__(self, center: int = 512, noise: int = 12) -> None:
        if not 0 <= center <= 1023 or noise < 0:
            raise ValueError("Invalid simulator configuration")
        self.center, self.noise = center, noise

    def read(self, channel: int = 0) -> int:
        validate_channel(channel)
        return max(0, min(1023, int(random.gauss(self.center, self.noise))))


def validate_channel(channel: int) -> None:
    if not 0 <= channel <= 7:
        raise ValueError("MCP3008 channel must be between 0 and 7")


@dataclass(frozen=True)
class Calibration:
    offset: float = 0.0
    slope: float = 1.0
    unit: str = "µε"

    def apply(self, raw: float) -> float:
        return (raw - self.offset) * self.slope

    @classmethod
    def from_two_points(cls, raw_a: float, known_a: float, raw_b: float, known_b: float, unit: str = "µε") -> "Calibration":
        if raw_a == raw_b:
            raise ValueError("Calibration ADC points must be different")
        slope = (known_b - known_a) / (raw_b - raw_a)
        return cls(offset=raw_a - known_a / slope, slope=slope, unit=unit)


@dataclass(frozen=True)
class Measurement:
    index: int
    timestamp: float
    timestamp_iso: str
    channel: int
    raw_average: float
    raw_std_dev: float
    calibrated_value: float
    unit: str
    sensor_id: str
    calibration_offset: float
    calibration_slope: float
    samples: tuple[int, ...]


@dataclass
class MeasurementSession:
    adc: ADCReader
    channel: int = 0
    samples_per_measurement: int = 35
    sample_delay_seconds: float = 0.01
    calibration_factor: float = 1.0
    calibration_offset: float = 0.0
    unit: str = "µε"
    sensor_id: str = "sensor-1"
    measurements: list[Measurement] = field(default_factory=list)
    _lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)

    def __post_init__(self) -> None:
        self.validate()

    @property
    def calibration(self) -> Calibration:
        return Calibration(self.calibration_offset, self.calibration_factor, self.unit)

    def validate(self) -> None:
        validate_channel(self.channel)
        if not 1 <= self.samples_per_measurement <= 100_000:
            raise ValueError("Samples must be between 1 and 100000")
        if not 0 <= self.sample_delay_seconds <= 60:
            raise ValueError("Sample delay must be between 0 and 60 seconds")
        if self.calibration_factor == 0:
            raise ValueError("Calibration slope cannot be zero")

    def measure(self) -> Measurement:
        with self._lock:
            self.validate()
            samples = self._read_samples()
            raw_average = stats.mean(samples)
            timestamp = time.time()
            measurement = Measurement(
                index=len(self.measurements) + 1,
                timestamp=timestamp,
                timestamp_iso=datetime.fromtimestamp(timestamp, timezone.utc).isoformat(),
                channel=self.channel,
                raw_average=raw_average,
                raw_std_dev=stats.pstdev(samples) if len(samples) > 1 else 0.0,
                calibrated_value=self.calibration.apply(raw_average),
                unit=self.unit,
                sensor_id=self.sensor_id,
                calibration_offset=self.calibration_offset,
                calibration_slope=self.calibration_factor,
                samples=tuple(samples),
            )
            self.measurements.append(measurement)
        return measurement

    def measure_many(self, count: int) -> list[Measurement]:
        if not 1 <= count <= 100_000:
            raise ValueError("Measurement count must be between 1 and 100000")
        return [self.measure() for _ in range(count)]

    def calibrate(self, known_value: float, readings: int = 29) -> float:
        if known_value <= 0:
            raise ValueError("One-point calibration value must be greater than zero")
        if readings < 1:
            raise ValueError("Calibration requires at least one reading")
        with self._lock:
            raw = stats.mean(stats.mean(self._read_samples()) for _ in range(readings))
            if raw == self.calibration_offset:
                raise ValueError("Calibration reference produces a zero denominator")
            self.calibration_factor = known_value / (raw - self.calibration_offset)
        return self.calibration_factor

    def calibrate_two_points(self, raw_a: float, known_a: float, raw_b: float, known_b: float) -> Calibration:
        calibration = Calibration.from_two_points(raw_a, known_a, raw_b, known_b, self.unit)
        self.calibration_offset, self.calibration_factor = calibration.offset, calibration.slope
        return calibration

    def reset(self) -> None:
        with self._lock:
            self.measurements.clear()

    def values(self) -> list[float]:
        with self._lock:
            return [item.calibrated_value for item in self.measurements]

    def summary(self) -> dict[str, float | int]:
        values = self.values()
        return {"count": len(values), "min": min(values, default=0.0), "max": max(values, default=0.0), "mean": stats.mean(values) if values else 0.0, "std_dev": stats.pstdev(values) if len(values) > 1 else 0.0}

    def _read_samples(self) -> list[int]:
        result = []
        for _ in range(self.samples_per_measurement):
            value = self.adc.read(self.channel)
            if not 0 <= value <= 1023:
                raise ValueError(f"ADC value outside MCP3008 range: {value}")
            result.append(value)
            if self.sample_delay_seconds:
                time.sleep(self.sample_delay_seconds)
        return result


def export_csv(path: str | Path, measurements: list[Measurement]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = [asdict(item) for item in measurements]
    fields = [name for name in Measurement.__dataclass_fields__ if name != "samples"] + ["samples"]
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            row["raw_average"] = f"{row['raw_average']:.6f}"
            row["raw_std_dev"] = f"{row['raw_std_dev']:.6f}"
            row["calibrated_value"] = f"{row['calibrated_value']:.6f}"
            row["samples"] = " ".join(map(str, row["samples"]))
            writer.writerow(row)
    return output


def export_json(path: str | Path, measurements: list[Measurement]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps([asdict(item) for item in measurements], ensure_ascii=False, indent=2), encoding="utf-8")
    return output
