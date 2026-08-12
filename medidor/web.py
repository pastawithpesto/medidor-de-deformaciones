from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict

from medidor.core import MeasurementSession
from medidor.hardware import create_adc
from medidor.i18n import translations

HTML = r'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Strain Live</title><script src="https://cdn.jsdelivr.net/npm/chart.js"></script><style>
:root{color-scheme:dark;--bg:#070b14;--panel:#101827;--line:#26344b;--text:#e7eefc;--muted:#91a0b8;--cyan:#23d5ff;--green:#42f5a7;--red:#ff5f7a}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 20% 0,#15233d,var(--bg) 38%);color:var(--text);font:15px system-ui,sans-serif}.top{display:flex;justify-content:space-between;align-items:center;padding:22px 4vw}.badge{padding:7px 12px;border:1px solid var(--cyan);border-radius:99px;color:var(--cyan)}main{display:grid;grid-template-columns:repeat(12,1fr);gap:16px;padding:0 4vw 4vw}.card{background:#101827dd;border:1px solid var(--line);border-radius:16px;padding:18px}.hero{grid-column:span 4}.chart{grid-column:span 8;min-height:390px}.controls,.stats{grid-column:span 6}.big{font-size:clamp(42px,8vw,86px);font-weight:750;color:var(--green)}.muted{color:var(--muted)}button,select,input{background:#0b1220;color:var(--text);border:1px solid var(--line);padding:10px 12px;border-radius:9px}button{cursor:pointer}button.primary{border-color:var(--cyan);color:var(--cyan)}.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.metric b{display:block;font-size:24px;margin-top:5px}.error{color:var(--red)}@media(max-width:850px){.hero,.chart,.controls,.stats{grid-column:1/-1}.grid{grid-template-columns:1fr 1fr}}
</style></head><body><header class="top"><div><h1 id="title">Medidor de deformaciones</h1><span class="muted">MCP3008 · WebSocket · REST API</span></div><div class="row"><span id="mode" class="badge"></span><select id="lang"><option value="es">Español</option><option value="en">English</option><option value="fr">Français</option><option value="zh">中文</option></select></div></header><main><section class="card hero"><span class="muted" data-t="value">Deformación</span><div><span class="big" id="value">--</span> <span id="unit">µε</span></div><div class="muted"><span data-t="raw">ADC</span>: <b id="raw">--</b></div><p id="status" class="muted">Connecting…</p></section><section class="card chart"><canvas id="plot"></canvas></section><section class="card controls"><h2>Control</h2><div class="row"><button class="primary" onclick="cmd('start')" data-t="start">Iniciar</button><button onclick="cmd('stop')" data-t="stop">Detener</button><button onclick="cmd('measure')" data-t="measure">Medir</button><button onclick="cmd('reset')" data-t="reset">Reiniciar</button></div></section><section class="card stats"><div class="grid"><div class="metric muted"><span data-t="samples">Muestras</span><b id="count">0</b></div><div class="metric muted"><span data-t="mean">Promedio</span><b id="mean">--</b></div><div class="metric muted"><span data-t="std">Desv.</span><b id="std">--</b></div></div></section></main><script>
const T=__TRANSLATIONS__;let lang=localStorage.lang||'es';document.querySelector('#lang').value=lang;const ctx=document.querySelector('#plot');const chart=new Chart(ctx,{type:'line',data:{labels:[],datasets:[{data:[],borderColor:'#23d5ff',backgroundColor:'#23d5ff22',fill:true,tension:.15,pointRadius:1}]},options:{responsive:true,maintainAspectRatio:false,animation:false,scales:{x:{ticks:{color:'#91a0b8'}},y:{ticks:{color:'#91a0b8'}}},plugins:{legend:{display:false}}}});function applyLang(){document.documentElement.lang=lang;document.querySelector('#title').textContent=T[lang].title;document.querySelectorAll('[data-t]').forEach(e=>e.textContent=T[lang][e.dataset.t]||e.dataset.t)}document.querySelector('#lang').onchange=e=>{lang=e.target.value;localStorage.lang=lang;applyLang()};applyLang();async function cmd(action){const r=await fetch('/api/'+action,{method:'POST'});if(!r.ok)document.querySelector('#status').textContent=await r.text()}function render(d){document.querySelector('#value').textContent=d.latest?d.latest.calibrated_value.toFixed(3):'--';document.querySelector('#raw').textContent=d.latest?d.latest.raw_average.toFixed(2):'--';document.querySelector('#unit').textContent=d.latest?d.latest.unit:'µε';document.querySelector('#count').textContent=d.summary.count;document.querySelector('#mean').textContent=d.summary.count?d.summary.mean.toFixed(3):'--';document.querySelector('#std').textContent=d.summary.count?d.summary.std_dev.toFixed(3):'--';document.querySelector('#mode').textContent=d.simulate?T[lang].simulation:T[lang].hardware;chart.data.labels=d.history.map(x=>x.index);chart.data.datasets[0].data=d.history.map(x=>x.calibrated_value);chart.update()}function connect(){const ws=new WebSocket((location.protocol==='https:'?'wss://':'ws://')+location.host+'/ws');ws.onopen=()=>document.querySelector('#status').textContent=T[lang].ready;ws.onmessage=e=>render(JSON.parse(e.data));ws.onclose=()=>{document.querySelector('#status').textContent='Reconnecting…';setTimeout(connect,1500)}}connect();
</script></body></html>'''


class LiveController:
    def __init__(self, session: MeasurementSession, simulate: bool, interval: float = 1.0) -> None:
        self.session, self.simulate, self.interval = session, simulate, interval
        self.running = False
        self.listeners: set[asyncio.Queue] = set()
        self.task: asyncio.Task | None = None

    def snapshot(self) -> dict:
        history = self.session.measurements[-500:]
        return {"simulate": self.simulate, "running": self.running, "latest": asdict(history[-1]) if history else None, "summary": self.session.summary(), "history": [asdict(x) for x in history]}

    async def publish(self) -> None:
        data = self.snapshot()
        for queue in tuple(self.listeners):
            if queue.full():
                queue.get_nowait()
            queue.put_nowait(data)

    async def measure(self) -> None:
        await asyncio.to_thread(self.session.measure)
        await self.publish()

    async def loop(self) -> None:
        while self.running:
            started = asyncio.get_running_loop().time()
            await self.measure()
            await asyncio.sleep(max(0, self.interval - (asyncio.get_running_loop().time() - started)))

    def start(self) -> None:
        if not self.running:
            self.running = True
            self.task = asyncio.create_task(self.loop())

    def stop(self) -> None:
        self.running = False


def create_web_app(session: MeasurementSession, simulate: bool = False, interval: float = 1.0):
    from fastapi import FastAPI, WebSocket
    from fastapi.responses import HTMLResponse
    app = FastAPI(title="Medidor de deformaciones API", version="0.3.0")
    live = LiveController(session, simulate, interval)

    @app.get("/", response_class=HTMLResponse)
    async def index():
        import json
        return HTML.replace("__TRANSLATIONS__", json.dumps(translations(), ensure_ascii=False))

    @app.get("/api/state")
    async def state(): return live.snapshot()

    @app.post("/api/start")
    async def start(): live.start(); return {"running": True}

    @app.post("/api/stop")
    async def stop(): live.stop(); return {"running": False}

    @app.post("/api/measure")
    async def measure(): await live.measure(); return live.snapshot()

    @app.post("/api/reset")
    async def reset(): session.reset(); await live.publish(); return live.snapshot()

    @app.websocket("/ws")
    async def websocket(websocket: WebSocket):
        await websocket.accept(); queue: asyncio.Queue = asyncio.Queue(maxsize=1); live.listeners.add(queue)
        try:
            await websocket.send_json(live.snapshot())
            while True: await websocket.send_json(await queue.get())
        finally: live.listeners.discard(queue)
    return app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate", action="store_true"); parser.add_argument("--host", default="127.0.0.1"); parser.add_argument("--port", type=int, default=8000); parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()
    import uvicorn
    session = MeasurementSession(create_adc(args.simulate))
    uvicorn.run(create_web_app(session, args.simulate, args.interval), host=args.host, port=args.port)


if __name__ == "__main__": main()
