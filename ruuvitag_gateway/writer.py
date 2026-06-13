"""Shared writer protocol for all backend services."""

from collections.abc import Callable

from ruuvitag_sensor.ruuvi_types import SensorData

from .configuration import Configuration, RuuviTagDevice


class WriterError(Exception):
    """Raised by any backend writer on failure."""


Writer = Callable[[Configuration, RuuviTagDevice, str, SensorData], None]
