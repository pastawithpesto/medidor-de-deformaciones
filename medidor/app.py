from __future__ import annotations

import argparse
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from medidor.core import MeasurementSession, export_csv, export_json
from medidor.hardware import create_adc
from medidor.reports import export_pdf


class MedidorApp(tk.Tk):
    def __init__(self, session: MeasurementSession, simulate: bool = False) -> None:
        super().__init__()
        self.session = session
        self.simulate = simulate
        self.title("Medidor de Deformaciones")
        self.geometry("1120x720")
        self.minsize(940, 620)

        self.status_text = tk.StringVar(value=self._startup_status())
        self.current_value = tk.StringVar(value="--")
        self.raw_value = tk.StringVar(value="--")
        self.count_value = tk.StringVar(value="0")
        self.mean_value = tk.StringVar(value="--")
        self.std_value = tk.StringVar(value="--")
        self.min_value = tk.StringVar(value="--")
        self.calibration_value = tk.StringVar(
            value=f"{self.session.calibration_factor:.6f}"
        )
        self.batch_count = tk.StringVar(value="10")
        self.known_value = tk.StringVar(value="")
        self.samples_value = tk.StringVar(value=str(self.session.samples_per_measurement))
        self.delay_value = tk.StringVar(value=str(self.session.sample_delay_seconds))

        self._build_style()
        self._build_layout()
        self._refresh_state()

    def _build_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        self.configure(bg="#f4f1ea")
        style.configure(".", font=("Helvetica", 10), background="#f4f1ea")
        style.configure("TFrame", background="#f4f1ea")
        style.configure("Panel.TFrame", background="#ffffff", relief="solid", borderwidth=1)
        style.configure("Muted.TLabel", foreground="#6b665d", background="#ffffff")
        style.configure("Value.TLabel", font=("Helvetica", 24, "bold"), background="#ffffff")
        style.configure("Stat.TLabel", font=("Helvetica", 15, "bold"), background="#ffffff")
        style.configure("Title.TLabel", font=("Helvetica", 13, "bold"), background="#ffffff")
        style.configure("Status.TLabel", foreground="#4b5563", background="#f4f1ea")
        style.configure("Accent.TButton", font=("Helvetica", 10, "bold"))

    def _build_layout(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=0, minsize=310)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(1, weight=1)

        header = ttk.Frame(root)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)
        ttk.Label(
            header,
            text="Medidor de Deformaciones",
            font=("Helvetica", 20, "bold"),
            background="#f4f1ea",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(header, textvariable=self.status_text, style="Status.TLabel").grid(
            row=1, column=0, sticky="w", pady=(3, 0)
        )

        left = ttk.Frame(root)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        right = ttk.Frame(root)
        right.grid(row=1, column=1, sticky="nsew")
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        self._build_reading_panel(left)
        self._build_controls_panel(left)
        self._build_export_panel(left)
        self._build_plot_panel(right)

    def _build_reading_panel(self, parent: ttk.Frame) -> None:
        panel = self._panel(parent, 0)
        ttk.Label(panel, text="Lectura actual", style="Title.TLabel").grid(
            row=0, column=0, sticky="w", columnspan=2
        )
        ttk.Label(panel, textvariable=self.current_value, style="Value.TLabel").grid(
            row=1, column=0, sticky="w", pady=(8, 0)
        )
        ttk.Label(panel, text="calibrado", style="Muted.TLabel").grid(
            row=1, column=1, sticky="s", padx=(8, 0), pady=(0, 5)
        )
        self._stat_grid(
            panel,
            2,
            [
                ("Mediciones", self.count_value),
                ("Promedio", self.mean_value),
                ("Desv. est.", self.std_value),
                ("Min / Max", self.min_value),
                ("ADC prom.", self.raw_value),
                ("Factor", self.calibration_value),
            ],
        )

    def _build_controls_panel(self, parent: ttk.Frame) -> None:
        panel = self._panel(parent, 1)
        ttk.Label(panel, text="Control", style="Title.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w"
        )
        ttk.Button(
            panel,
            text="Medir",
            style="Accent.TButton",
            command=self._measure_once,
        ).grid(row=1, column=0, sticky="ew", pady=(10, 8))
        ttk.Button(panel, text="Lote", command=self._measure_batch).grid(
            row=1, column=1, sticky="ew", padx=6, pady=(10, 8)
        )
        ttk.Button(panel, text="Reset", command=self._reset).grid(
            row=1, column=2, sticky="ew", pady=(10, 8)
        )

        self._labeled_entry(panel, "Lote", self.batch_count, 2, 0)
        self._labeled_entry(panel, "Muestras", self.samples_value, 2, 1)
        self._labeled_entry(panel, "Pausa s", self.delay_value, 2, 2)

        ttk.Separator(panel).grid(row=4, column=0, columnspan=3, sticky="ew", pady=12)
        self._labeled_entry(panel, "Valor conocido", self.known_value, 5, 0, colspan=2)
        ttk.Button(panel, text="Calibrar", command=self._calibrate).grid(
            row=6, column=2, sticky="ew", padx=(6, 0)
        )

        for column in range(3):
            panel.columnconfigure(column, weight=1)

    def _build_export_panel(self, parent: ttk.Frame) -> None:
        panel = self._panel(parent, 2)
        ttk.Label(panel, text="Exportar", style="Title.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w"
        )
        ttk.Button(panel, text="CSV", command=self._save_csv).grid(
            row=1, column=0, sticky="ew", pady=(10, 0)
        )
        ttk.Button(panel, text="JSON", command=self._save_json).grid(
            row=1, column=1, sticky="ew", padx=6, pady=(10, 0)
        )
        ttk.Button(panel, text="PDF", command=self._save_pdf).grid(
            row=1, column=2, sticky="ew", pady=(10, 0)
        )
        for column in range(3):
            panel.columnconfigure(column, weight=1)

    def _build_plot_panel(self, parent: ttk.Frame) -> None:
        panel = self._panel(parent, 0)
        panel.rowconfigure(1, weight=1)
        panel.columnconfigure(0, weight=1)
        ttk.Label(panel, text="Sesion", style="Title.TLabel").grid(row=0, column=0, sticky="w")

        self.figure = Figure(figsize=(6, 4), dpi=100, facecolor="#ffffff")
        self.axes = self.figure.add_subplot(111)
        self.axes.set_facecolor("#ffffff")
        self.axes.grid(True, color="#e5e0d8")
        self.axes.set_xlabel("Medicion")
        self.axes.set_ylabel("Valor calibrado")
        (self.plot_line,) = self.axes.plot([], [], color="#1f6f78", linewidth=2)
        self.canvas = FigureCanvasTkAgg(self.figure, master=panel)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew", pady=(10, 0))

    def _panel(self, parent: ttk.Frame, row: int) -> ttk.Frame:
        panel = ttk.Frame(parent, padding=14, style="Panel.TFrame")
        panel.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        panel.columnconfigure(0, weight=1)
        return panel

    def _stat_grid(
        self,
        parent: ttk.Frame,
        start_row: int,
        rows: list[tuple[str, tk.StringVar]],
    ) -> None:
        for offset, (label, variable) in enumerate(rows):
            row = start_row + offset // 2
            column = (offset % 2) * 2
            ttk.Label(parent, text=label, style="Muted.TLabel").grid(
                row=row,
                column=column,
                sticky="w",
                pady=(12, 0),
            )
            ttk.Label(parent, textvariable=variable, style="Stat.TLabel").grid(
                row=row,
                column=column + 1,
                sticky="e",
                padx=(8, 0),
                pady=(12, 0),
            )
            parent.columnconfigure(column + 1, weight=1)

    def _labeled_entry(
        self,
        parent: ttk.Frame,
        label: str,
        variable: tk.StringVar,
        row: int,
        column: int,
        colspan: int = 1,
    ) -> None:
        ttk.Label(parent, text=label, style="Muted.TLabel").grid(
            row=row,
            column=column,
            sticky="w",
            columnspan=colspan,
        )
        ttk.Entry(parent, textvariable=variable).grid(
            row=row + 1,
            column=column,
            columnspan=colspan,
            sticky="ew",
            pady=(3, 0),
        )

    def _measure_once(self) -> None:
        try:
            self._apply_sampling_config()
        except ValueError as exc:
            messagebox.showerror("Configuracion invalida", str(exc))
            return
        measurement = self.session.measure()
        self.status_text.set(f"Medicion {measurement.index} registrada.")
        self._refresh_state()

    def _measure_batch(self) -> None:
        try:
            self._apply_sampling_config()
            count = int(self.batch_count.get())
            self.session.measure_many(count)
        except ValueError as exc:
            messagebox.showerror("Medicion invalida", str(exc))
            return
        self.status_text.set(f"{count} mediciones registradas.")
        self._refresh_state()

    def _calibrate(self) -> None:
        try:
            self._apply_sampling_config()
            known_value = float(self.known_value.get())
            factor = self.session.calibrate(known_value)
        except ValueError as exc:
            messagebox.showerror("Calibracion invalida", str(exc))
            return
        self.status_text.set(f"Calibracion actualizada: factor {factor:.6f}.")
        self._refresh_state()

    def _reset(self) -> None:
        self.session.reset()
        self.status_text.set("Sesion reiniciada.")
        self._refresh_state()

    def _save_csv(self) -> None:
        path = self._ask_output_path("mediciones.csv", [("CSV", "*.csv")])
        if path:
            export_csv(path, self.session.measurements)
            self.status_text.set(f"CSV guardado en {path}.")

    def _save_json(self) -> None:
        path = self._ask_output_path("mediciones.json", [("JSON", "*.json")])
        if path:
            export_json(path, self.session.measurements)
            self.status_text.set(f"JSON guardado en {path}.")

    def _save_pdf(self) -> None:
        default_name = "reporte_" + time.strftime("%Y%m%d_%H%M%S") + ".pdf"
        path = self._ask_output_path(default_name, [("PDF", "*.pdf")])
        if path:
            export_pdf(path, self.session)
            self.status_text.set(f"PDF guardado en {path}.")

    def _ask_output_path(
        self,
        default_name: str,
        filetypes: list[tuple[str, str]],
    ) -> Path | None:
        if not self.session.measurements:
            messagebox.showinfo("Sin mediciones", "Toma al menos una medicion primero.")
            return None
        selected = filedialog.asksaveasfilename(
            initialfile=default_name,
            defaultextension=Path(default_name).suffix,
            filetypes=filetypes,
        )
        return Path(selected) if selected else None

    def _apply_sampling_config(self) -> None:
        try:
            samples = int(self.samples_value.get())
            delay = float(self.delay_value.get())
        except ValueError as exc:
            raise ValueError("Muestras y pausa deben ser numeros validos.") from exc
        if samples < 1:
            raise ValueError("Muestras debe ser mayor que cero.")
        if delay < 0:
            raise ValueError("Pausa no puede ser negativa.")
        self.session.samples_per_measurement = samples
        self.session.sample_delay_seconds = delay

    def _refresh_state(self) -> None:
        summary = self.session.summary()
        values = self.session.values()
        latest = self.session.measurements[-1] if self.session.measurements else None

        self.count_value.set(str(summary["count"]))
        self.current_value.set(f"{latest.calibrated_value:.3f}" if latest else "--")
        self.raw_value.set(f"{latest.raw_average:.2f}" if latest else "--")
        self.mean_value.set(f"{summary['mean']:.3f}" if values else "--")
        self.std_value.set(f"{summary['std_dev']:.3f}" if values else "--")
        if values:
            self.min_value.set(f"{summary['min']:.3f} / {summary['max']:.3f}")
        else:
            self.min_value.set("--")
        self.calibration_value.set(f"{self.session.calibration_factor:.6f}")
        self._refresh_plot()

    def _refresh_plot(self) -> None:
        values = self.session.values()
        x_values = list(range(1, len(values) + 1))
        self.plot_line.set_data(x_values, values)
        self.axes.relim()
        self.axes.autoscale_view()
        if not values:
            self.axes.set_xlim(0, 1)
            self.axes.set_ylim(0, 1)
        self.canvas.draw_idle()

    def _startup_status(self) -> str:
        if self.simulate:
            return "Modo simulacion: no se usara hardware SPI."
        return "Listo. Si no hay MCP3008 disponible, se usa simulacion automaticamente."


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Medidor de deformaciones")
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="usar lecturas simuladas en lugar del MCP3008",
    )
    parser.add_argument("--channel", type=int, default=0, help="canal MCP3008")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    adc = create_adc(simulate=args.simulate)
    session = MeasurementSession(adc=adc, channel=args.channel)
    app = MedidorApp(session=session, simulate=args.simulate)
    app.mainloop()


if __name__ == "__main__":
    main()
