from __future__ import annotations

from medidor.core import ADCReader, SimulatedADC, validate_channel


class HardwareUnavailableError(RuntimeError):
    pass


class CircuitPythonMCP3008:
    def __init__(self, chip_select_pin: int = 8) -> None:
        import board
        import busio
        import digitalio
        import adafruit_mcp3xxx.mcp3008 as MCP
        from adafruit_mcp3xxx.analog_in import AnalogIn

        pin = getattr(board, f"D{chip_select_pin}")
        spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        chip_select = digitalio.DigitalInOut(pin)
        self._mcp = MCP.MCP3008(spi, chip_select)
        self._channels = [AnalogIn(self._mcp, p) for p in (MCP.P0, MCP.P1, MCP.P2, MCP.P3, MCP.P4, MCP.P5, MCP.P6, MCP.P7)]

    def read(self, channel: int = 0) -> int:
        validate_channel(channel)
        return int(round(self._channels[channel].value * 1023 / 65535))


def create_adc(simulate: bool = False) -> ADCReader:
    if simulate:
        return SimulatedADC()
    try:
        return CircuitPythonMCP3008()
    except Exception as exc:
        raise HardwareUnavailableError(
            "MCP3008 unavailable. Check SPI, wiring and permissions, or start explicitly with --simulate."
        ) from exc
