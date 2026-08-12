from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_PATH = Path.home() / ".config" / "medidor-de-deformaciones" / "settings.json"


@dataclass
class Settings:
    language: str = "es"
    channel: int = 0
    samples_per_measurement: int = 35
    sample_delay_seconds: float = 0.01
    interval_seconds: float = 1.0
    calibration_offset: float = 0.0
    calibration_slope: float = 1.0
    unit: str = "µε"
    sensor_id: str = "sensor-1"

    @classmethod
    def load(cls, path: Path = DEFAULT_PATH) -> "Settings":
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        allowed = cls.__dataclass_fields__.keys()
        return cls(**{key: value for key, value in data.items() if key in allowed})

    def save(self, path: Path = DEFAULT_PATH) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")
        return path
