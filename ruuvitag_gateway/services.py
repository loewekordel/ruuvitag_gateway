"""
This module provides a mapping of service names to their respective write functions.
"""

from .cloud import write_thingspeak
from .database import write_influxdb

SERVICE_MAP = {
    "influxdb": write_influxdb,
    "thingspeak": write_thingspeak,
}
