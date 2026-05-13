# Medidor de Deformaciones

Aplicacion de escritorio para tomar mediciones con un ADC MCP3008 en Raspberry Pi,
calibrarlas, graficarlas y exportarlas como CSV, JSON o PDF.

El proyecto original era un unico script de Tkinter. Esta version separa la logica
de medicion, la interfaz, el acceso al hardware y los reportes para que sea mas
facil de probar y mantener.

## Funciones

- Interfaz Tkinter redisenada con lectura actual, resumen estadistico y grafica.
- Lecturas por lote con numero de muestras y pausa configurables.
- Calibracion por valor conocido.
- Exportacion a CSV, JSON y PDF.
- Modo simulacion para desarrollar sin Raspberry Pi ni MCP3008.
- CLI para uso sin interfaz grafica.

## Hardware

Configuracion esperada:

- Raspberry Pi con SPI habilitado.
- MCP3008 conectado por SPI.
- Sensor conectado al canal `CH0` por defecto.

Conexiones tipicas del MCP3008:

| MCP3008 | Raspberry Pi |
| --- | --- |
| VDD, VREF | 3.3V |
| AGND, DGND | GND |
| CLK | SCLK / GPIO11 |
| DOUT | MISO / GPIO9 |
| DIN | MOSI / GPIO10 |
| CS | CE0 / GPIO8 |

## Instalacion

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

En Raspberry Pi, habilita SPI con `raspi-config` antes de ejecutar la app.

## Uso

Interfaz grafica:

```bash
python medef.py
```

Modo simulacion:

```bash
python medef.py --simulate
```

CLI:

```bash
medidor-medicion --simulate --count 20 --csv mediciones.csv
```

## Calibracion

1. Coloca una carga o referencia conocida.
2. Escribe el valor conocido en la interfaz.
3. Presiona `Calibrar`.

La app calcula:

```text
factor = valor_conocido / promedio_adc
valor_calibrado = promedio_adc * factor
```

## Desarrollo

Ejecuta las pruebas:

```bash
python -m unittest discover -s tests
```

El modo simulacion permite probar la interfaz y los exportadores sin hardware.
