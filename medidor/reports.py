from __future__ import annotations

from pathlib import Path

from medidor.core import MeasurementSession

MM = 72 / 25.4


def export_pdf(path: str | Path, session: MeasurementSession) -> Path:
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table

    output = Path(path); output.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet(); summary = session.summary()
    document = SimpleDocTemplate(str(output), pagesize=landscape(letter), rightMargin=12*mm, leftMargin=12*mm, topMargin=15*mm, bottomMargin=15*mm)
    story = [Paragraph("Measurement report / Reporte de mediciones", styles["Title"]), Spacer(1, 5*mm)]
    summary_data = [["Count", "Minimum", "Maximum", "Average", "Std. deviation", "Offset", "Slope", "Unit"], [summary["count"], f"{summary['min']:.6f}", f"{summary['max']:.6f}", f"{summary['mean']:.6f}", f"{summary['std_dev']:.6f}", f"{session.calibration_offset:.8f}", f"{session.calibration_factor:.8f}", session.unit]]
    summary_table = Table(summary_data, repeatRows=1); summary_table.setStyle(_table_style()); story += [summary_table, Spacer(1, 8*mm)]
    rows = [["#", "UTC timestamp", "Sensor", "CH", "ADC mean", "ADC σ", "Value", "Unit", "Offset", "Slope"]]
    rows += [[m.index, m.timestamp_iso, m.sensor_id, m.channel, f"{m.raw_average:.4f}", f"{m.raw_std_dev:.4f}", f"{m.calibrated_value:.6f}", m.unit, f"{m.calibration_offset:.6f}", f"{m.calibration_slope:.8f}"] for m in session.measurements]
    table = Table(rows, repeatRows=1, colWidths=[10*mm, 45*mm, 25*mm, 9*mm, 22*mm, 18*mm, 24*mm, 13*mm, 23*mm, 24*mm]); table.setStyle(_table_style()); story.append(table)
    document.build(story, onFirstPage=_page_number, onLaterPages=_page_number)
    return output


def _table_style():
    from reportlab.lib import colors
    from reportlab.platypus import TableStyle
    return TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#18324a")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),7),("GRID",(0,0),(-1,-1),.25,colors.HexColor("#9aa8b5")),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#eef4f7")]),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4)])


def _page_number(canvas, document):
    canvas.saveState(); canvas.setFont("Helvetica", 8); canvas.drawRightString(document.pagesize[0]-12*MM, 8*MM, f"Page {document.page}"); canvas.restoreState()
