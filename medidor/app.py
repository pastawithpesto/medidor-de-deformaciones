from __future__ import annotations

import argparse
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from medidor.core import MeasurementSession, export_csv, export_json
from medidor.hardware import HardwareUnavailableError, create_adc
from medidor.i18n import LANGUAGES, tr
from medidor.settings import Settings
from medidor.reports import export_pdf


class MedidorApp(tk.Tk):
    def __init__(self, session: MeasurementSession, settings: Settings, simulate: bool) -> None:
        super().__init__(); self.session=session; self.settings=settings; self.simulate=simulate
        self.running=False; self.busy=False; self.events: queue.Queue=queue.Queue(); self.protocol("WM_DELETE_WINDOW", self.close)
        self.geometry("980x660"); self.configure(bg="#07101d"); self.columnconfigure(0,weight=1); self.rowconfigure(1,weight=1)
        self.language=tk.StringVar(value=settings.language); self.value=tk.StringVar(value="--"); self.raw=tk.StringVar(value="--"); self.status=tk.StringVar(); self.stats=tk.StringVar(value="0")
        self.samples=tk.StringVar(value=str(settings.samples_per_measurement)); self.delay=tk.StringVar(value=str(settings.sample_delay_seconds)); self.known=tk.StringVar()
        self._build(); self.retranslate(); self.after(100,self._poll)

    def _build(self):
        style=ttk.Style(self); style.theme_use("clam"); style.configure(".",background="#101b2d",foreground="#e8f0ff",fieldbackground="#07101d"); style.configure("TButton",padding=9); style.configure("TLabel",padding=4)
        top=ttk.Frame(self,padding=16); top.grid(sticky="ew"); top.columnconfigure(0,weight=1); self.title_label=ttk.Label(top,font=("Helvetica",22,"bold")); self.title_label.grid(row=0,column=0,sticky="w")
        self.language_box=ttk.Combobox(top,textvariable=self.language,values=list(LANGUAGES),state="readonly",width=5); self.language_box.grid(row=0,column=1); self.language_box.bind("<<ComboboxSelected>>",lambda _:self.retranslate())
        main=ttk.Frame(self,padding=16); main.grid(row=1,sticky="nsew"); main.columnconfigure((0,1),weight=1); main.rowconfigure(0,weight=1)
        left=ttk.LabelFrame(main,padding=18); left.grid(row=0,column=0,sticky="nsew",padx=(0,8)); right=ttk.LabelFrame(main,padding=18); right.grid(row=0,column=1,sticky="nsew",padx=(8,0))
        self.value_label=ttk.Label(left); self.value_label.pack(anchor="w"); ttk.Label(left,textvariable=self.value,font=("Helvetica",58,"bold"),foreground="#39efb0").pack(anchor="w"); ttk.Label(left,textvariable=self.raw,font=("Helvetica",16)).pack(anchor="w"); ttk.Label(left,textvariable=self.stats,wraplength=400).pack(anchor="w",pady=18)
        controls=ttk.Frame(left); controls.pack(fill="x"); self.buttons={k:ttk.Button(controls,command=fn) for k,fn in {"measure":self.measure,"start":self.start,"stop":self.stop,"reset":self.reset}.items()}
        for i,b in enumerate(self.buttons.values()): b.grid(row=0,column=i,padx=3,sticky="ew"); controls.columnconfigure(i,weight=1)
        self.entries={};
        for key,var in (("samples",self.samples),("delay",self.delay),("known",self.known)):
            label=ttk.Label(right); label.pack(anchor="w",pady=(8,0)); entry=ttk.Entry(right,textvariable=var); entry.pack(fill="x"); self.entries[key]=(label,entry)
        self.calibrate_button=ttk.Button(right,command=self.calibrate); self.calibrate_button.pack(fill="x",pady=12); self.export_button=ttk.Button(right,command=self.export); self.export_button.pack(fill="x")
        ttk.Label(self,textvariable=self.status,padding=12).grid(row=2,sticky="ew")

    def retranslate(self):
        lang=self.language.get(); self.settings.language=lang; self.title(tr(lang,"title")); self.title_label.configure(text=tr(lang,"title")); self.value_label.configure(text=tr(lang,"value"))
        for key,button in self.buttons.items(): button.configure(text=tr(lang,key))
        for key,(label,_) in self.entries.items(): label.configure(text=tr(lang,key))
        self.calibrate_button.configure(text=tr(lang,"calibrate")); self.export_button.configure(text=tr(lang,"export")); self.status.set(f"{tr(lang,'ready')} · {tr(lang,'simulation' if self.simulate else 'hardware')}")

    def _config(self):
        samples=int(self.samples.get()); delay=float(self.delay.get()); self.session.samples_per_measurement=samples; self.session.sample_delay_seconds=delay; self.session.validate(); self.settings.samples_per_measurement=samples; self.settings.sample_delay_seconds=delay

    def _work(self, fn):
        if self.busy:
            return
        self.busy=True
        def run():
            try: fn(); self.events.put(None)
            except Exception as exc: self.events.put(exc)
        threading.Thread(target=run,daemon=True).start()

    def measure(self):
        try:self._config()
        except Exception as exc:return messagebox.showerror(tr(self.language.get(),"error"),str(exc))
        self._work(self.session.measure)

    def start(self): self.running=True; self._continuous()
    def stop(self): self.running=False
    def _continuous(self):
        if self.running: self.measure(); self.after(max(100,int(self.settings.interval_seconds*1000)),self._continuous)
    def reset(self): self.session.reset(); self.refresh()
    def calibrate(self):
        try:self._config(); known=float(self.known.get()); self._work(lambda:self.session.calibrate(known))
        except Exception as exc:messagebox.showerror(tr(self.language.get(),"error"),str(exc))
    def export(self):
        if not self.session.measurements:return
        path=filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV","*.csv"),("JSON","*.json"),("PDF","*.pdf")]);
        if path:
            suffix=Path(path).suffix.lower()
            if suffix==".json":export_json(Path(path),self.session.measurements)
            elif suffix==".pdf":export_pdf(Path(path),self.session)
            else:export_csv(Path(path),self.session.measurements)
    def _poll(self):
        try:
            while True:
                event=self.events.get_nowait()
                self.busy=False
                if isinstance(event,Exception): messagebox.showerror(tr(self.language.get(),"error"),str(event))
                self.refresh()
        except queue.Empty:pass
        self.after(100,self._poll)
    def refresh(self):
        s=self.session.summary(); latest=self.session.measurements[-1] if self.session.measurements else None; self.value.set(f"{latest.calibrated_value:.3f} {latest.unit}" if latest else "--"); self.raw.set(f"ADC: {latest.raw_average:.2f}" if latest else "ADC: --"); self.stats.set(f"n={s['count']}  mean={s['mean']:.3f}  min={s['min']:.3f}  max={s['max']:.3f}  σ={s['std_dev']:.3f}")
    def close(self): self.running=False; self.settings.calibration_offset=self.session.calibration_offset; self.settings.calibration_slope=self.session.calibration_factor; self.settings.save(); self.destroy()


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--simulate",action="store_true"); args=parser.parse_args(); settings=Settings.load()
    try:adc=create_adc(args.simulate)
    except HardwareUnavailableError as exc: raise SystemExit(str(exc)) from exc
    session=MeasurementSession(adc,channel=settings.channel,samples_per_measurement=settings.samples_per_measurement,sample_delay_seconds=settings.sample_delay_seconds,calibration_factor=settings.calibration_slope,calibration_offset=settings.calibration_offset,unit=settings.unit,sensor_id=settings.sensor_id)
    MedidorApp(session,settings,args.simulate).mainloop()


if __name__=="__main__":main()
