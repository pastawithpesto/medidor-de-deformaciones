# Medidor de deformaciones · Strain gauge monitor · Mesureur de déformations · 应变测量仪

Sistema para adquirir, calibrar, visualizar y exportar mediciones de un MCP3008 conectado a una Raspberry Pi. Incluye aplicación de escritorio, CLI y dashboard web en tiempo real.

## Español

### Funciones

- Dashboard web responsivo con WebSocket, gráfica en vivo y API REST.
- Aplicación Tkinter sin bloqueos durante adquisición o calibración.
- Español, inglés, francés y chino en las interfaces.
- Lectura manual, continua y por CLI.
- Calibración de un punto y modelo lineal de dos puntos.
- Offset, pendiente, unidad física e identificador de sensor.
- Persistencia local de configuración y calibración.
- Exportación CSV y JSON con fecha UTC ISO 8601, muestras crudas y metadatos.
- Modo simulado explícito para desarrollo sin hardware.
- Validación de canal, rango ADC, muestras, pausa y calibración.
- Una falla del MCP3008 detiene el arranque. Nunca genera datos simulados sin avisar.

### Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[web]"
```

En Raspberry Pi activa SPI con `sudo raspi-config`, conecta el MCP3008 y confirma que el usuario tenga acceso a SPI.

### Aplicación de escritorio

```bash
medidor-de-deformaciones
medidor-de-deformaciones --simulate
```

### Dashboard web en tiempo real

```bash
medidor-web --host 0.0.0.0 --port 8000
medidor-web --simulate --host 0.0.0.0 --port 8000 --interval 0.5
```

Abre `http://IP-DE-LA-RASPBERRY:8000`. No expongas el puerto directamente a Internet. Para uso remoto agrega autenticación, HTTPS y un proxy como Nginx o Caddy.

API principal:

| Método | Ruta | Función |
|---|---|---|
| `GET` | `/api/state` | Estado, resumen e historial reciente |
| `POST` | `/api/start` | Inicia adquisición continua |
| `POST` | `/api/stop` | Detiene adquisición |
| `POST` | `/api/measure` | Registra una medición |
| `POST` | `/api/reset` | Borra la sesión en memoria |
| WebSocket | `/ws` | Publica cambios en tiempo real |

### Calibración

El modelo es:

```text
valor = (ADC_promedio - offset) × pendiente
```

La calibración de un punto conserva el offset actual y calcula la pendiente. La calibración de dos puntos calcula ambos parámetros. Para galgas extensométricas, documenta la ganancia del amplificador, voltaje de excitación, configuración del puente y factor de galga. El MCP3008 solo mide voltaje: convertirlo a `µε` requiere esa cadena física de calibración.

### Datos

Cada registro contiene índice, fecha UTC, canal, promedio ADC, desviación ADC, valor calibrado, unidad, sensor, offset, pendiente y todas las muestras crudas. El dashboard conserva y transmite las últimas 500 mediciones para evitar crecimiento ilimitado del tráfico.

## English

This project reads an MCP3008 on Raspberry Pi and provides a non-blocking Tkinter UI, command-line acquisition, and a responsive real-time web dashboard. The WebSocket sends live measurements while the REST endpoints control acquisition. Configuration and calibration persist locally. Hardware failures stop startup instead of silently switching to simulated data.

Install with `pip install -e ".[web]"`. Run `medidor-de-deformaciones` for desktop, `medidor-web --host 0.0.0.0` for the dashboard, or add `--simulate` explicitly when no MCP3008 is connected.

The calibration equation is `value = (ADC average - offset) × slope`. A physical strain result also depends on the bridge, excitation voltage, amplifier gain and gauge factor.

## Français

Ce projet lit un MCP3008 sur Raspberry Pi et fournit une interface Tkinter non bloquante, une CLI et un tableau de bord web en temps réel. WebSocket transmet les mesures, tandis que l’API REST contrôle l’acquisition. La configuration et l’étalonnage sont enregistrés localement. Une panne matérielle arrête le démarrage au lieu d’activer une simulation invisible.

Installez avec `pip install -e ".[web]"`. Lancez `medidor-de-deformaciones`, `medidor-web --host 0.0.0.0`, ou ajoutez explicitement `--simulate` sans matériel.

Le modèle est `valeur = (moyenne CAN - offset) × pente`. La conversion physique exige aussi la configuration du pont, la tension d’excitation, le gain et le facteur de jauge.

## 中文

本项目通过树莓派读取 MCP3008，并提供非阻塞 Tkinter 桌面界面、命令行采集和实时网页仪表板。WebSocket 推送实时测量结果，REST API 控制采集。配置和校准参数保存在本地。硬件故障会停止启动，不会在未通知用户的情况下切换到模拟数据。

使用 `pip install -e ".[web]"` 安装。运行 `medidor-de-deformaciones` 启动桌面界面，运行 `medidor-web --host 0.0.0.0` 启动网页界面。未连接硬件时必须明确添加 `--simulate`。

校准公式为 `测量值 =（ADC 平均值 - 偏移量）× 斜率`。要得到真实应变值，还必须知道电桥结构、激励电压、放大器增益和应变片灵敏系数。

## Desarrollo y pruebas

```bash
pip install -e ".[web,dev]"
pytest --cov=medidor
ruff check .
```

Los datos simulados son solo para desarrollo y demostración. No sirven para validar precisión, repetibilidad ni seguridad de un instrumento físico.
