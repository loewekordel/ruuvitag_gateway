"""Registry mapping service names to their writer functions."""

from .cloud import write_thingspeak
from .database import write_influxdb
from .writer import Writer

SERVICE_MAP: dict[str, Writer] = {
    "influxdb": write_influxdb,
    "thingspeak": write_thingspeak,
}
