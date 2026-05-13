from __future__ import annotations

import time
from pathlib import Path

from medidor.core import Measurement, MeasurementSession


def export_pdf(path: str | Path, session: MeasurementSession) -> Path:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    output_path = Path(path)
    summary = session.summary()
    report = canvas.Canvas(str(output_path), pagesize=letter)
    report.setTitle("Reporte de mediciones")

    report.setFont("Helvetica-Bold", 16)
    report.drawString(72, 735, "Reporte de mediciones")
    report.setFont("Helvetica", 10)
    report.drawString(
        72,
        715,
        "Generado: "
        + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
    )

    report.setFont("Helvetica-Bold", 12)
    report.drawString(72, 680, "Resumen")
    report.setFont("Helvetica", 10)
    rows = [
        ("Mediciones", summary["count"]),
        ("Minimo", f"{summary['min']:.3f}"),
        ("Maximo", f"{summary['max']:.3f}"),
        ("Promedio", f"{summary['mean']:.3f}"),
        ("Desv. estandar", f"{summary['std_dev']:.3f}"),
        ("Factor calibracion", f"{session.calibration_factor:.8f}"),
    ]
    y = 660
    for label, value in rows:
        report.drawString(72, y, f"{label}: {value}")
        y -= 18

    report.setFont("Helvetica-Bold", 12)
    report.drawString(72, y - 12, "Ultimas mediciones")
    y -= 34
    report.setFont("Helvetica", 9)
    report.drawString(72, y, "No.     Fecha                Valor calibrado     Prom. ADC")
    y -= 14
    for measurement in session.measurements[-20:]:
        report.drawString(72, y, _measurement_row(measurement))
        y -= 14
        if y < 72:
            report.showPage()
            y = 735

    report.save()
    return output_path


def _measurement_row(measurement: Measurement) -> str:
    timestamp = time.strftime(
        "%Y-%m-%d %H:%M:%S",
        time.localtime(measurement.timestamp),
    )
    return (
        f"{measurement.index:<7} "
        f"{timestamp:<20} "
        f"{measurement.calibrated_value:<18.3f} "
        f"{measurement.raw_average:.3f}"
    )

