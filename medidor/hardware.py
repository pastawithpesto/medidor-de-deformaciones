from __future__ import annotations

from medidor.core import ADCReader, SimulatedADC


class CircuitPythonMCP3008:
    """MCP3008 reader using Adafruit's current CircuitPython library."""

    def __init__(self) -> None:
        import board
        import busio
        import digitalio
        import adafruit_mcp3xxx.mcp3008 as MCP
        from adafruit_mcp3xxx.analog_in import AnalogIn

        spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        chip_select = digitalio.DigitalInOut(board.D8)
        self._mcp = MCP.MCP3008(spi, chip_select)
        pins = [MCP.P0, MCP.P1, MCP.P2, MCP.P3, MCP.P4, MCP.P5, MCP.P6, MCP.P7]
        self._channels = [AnalogIn(self._mcp, pin) for pin in pins]

    def read(self, channel: int = 0) -> int:
        return int(self._channels[channel].value * 1023 / 65535)


def create_adc(simulate: bool = False) -> ADCReader:
    if simulate:
        return SimulatedADC()

    try:
        return CircuitPythonMCP3008()
    except Exception:
        return SimulatedADC()
