from __future__ import annotations

LANGUAGES = {"es": "Español", "en": "English", "fr": "Français", "zh": "中文"}

_TEXT = {
    "es": {"title": "Medidor de deformaciones", "status": "Estado", "value": "Deformación", "raw": "ADC", "mean": "Promedio", "std": "Desv. estándar", "samples": "Muestras", "delay": "Pausa (s)", "known": "Valor conocido", "measure": "Medir", "start": "Iniciar", "stop": "Detener", "reset": "Reiniciar", "calibrate": "Calibrar", "export": "Exportar", "ready": "Listo", "simulation": "SIMULACIÓN", "hardware": "HARDWARE", "error": "Error", "language": "Idioma"},
    "en": {"title": "Strain gauge monitor", "status": "Status", "value": "Strain", "raw": "ADC", "mean": "Average", "std": "Std. deviation", "samples": "Samples", "delay": "Delay (s)", "known": "Known value", "measure": "Measure", "start": "Start", "stop": "Stop", "reset": "Reset", "calibrate": "Calibrate", "export": "Export", "ready": "Ready", "simulation": "SIMULATION", "hardware": "HARDWARE", "error": "Error", "language": "Language"},
    "fr": {"title": "Mesureur de déformations", "status": "État", "value": "Déformation", "raw": "CAN", "mean": "Moyenne", "std": "Écart-type", "samples": "Échantillons", "delay": "Pause (s)", "known": "Valeur connue", "measure": "Mesurer", "start": "Démarrer", "stop": "Arrêter", "reset": "Réinitialiser", "calibrate": "Étalonner", "export": "Exporter CSV", "ready": "Prêt", "simulation": "SIMULATION", "hardware": "MATÉRIEL", "error": "Erreur", "language": "Langue"},
    "zh": {"title": "应变测量仪", "status": "状态", "value": "应变", "raw": "ADC", "mean": "平均值", "std": "标准差", "samples": "样本数", "delay": "间隔（秒）", "known": "已知值", "measure": "测量", "start": "开始", "stop": "停止", "reset": "重置", "calibrate": "校准", "export": "导出 CSV", "ready": "就绪", "simulation": "模拟", "hardware": "硬件", "error": "错误", "language": "语言"},
}


def tr(language: str, key: str) -> str:
    return _TEXT.get(language, _TEXT["es"]).get(key, key)


def translations() -> dict[str, dict[str, str]]:
    return _TEXT
