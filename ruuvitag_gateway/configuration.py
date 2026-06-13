"""Configuration module for the ruuvitag gateway application."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError, model_validator


class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""


class RuuviTagDevice(BaseModel):
    """A single RuuviTag device."""

    mac: str
    name: str


class RuuviTagConfiguration(BaseModel):
    """RuuviTag scanning configuration."""

    devices: list[RuuviTagDevice]
    scan_duration_sec: int = 10


class InfluxDBConfiguration(BaseModel):
    """InfluxDB connection configuration."""

    host: str
    port: int = 8086
    database: str
    measurements: dict[str, str] = {}


class ThingspeakConfiguration(BaseModel):
    """ThingSpeak channel configuration."""

    channel_id: int
    api_key: str
    fields: dict[str, int]


class ServicesConfiguration(BaseModel):
    """Selects which backend services are active."""

    database: str | None = None
    cloud: str | None = None


class Configuration(BaseModel):
    """Top-level gateway configuration."""

    ruuvitag: RuuviTagConfiguration
    services: ServicesConfiguration = ServicesConfiguration()
    influxdb: InfluxDBConfiguration | None = None
    thingspeak: ThingspeakConfiguration | None = None

    @model_validator(mode="after")
    def at_least_one_backend(self) -> Configuration:
        """Ensure that at least one backend (InfluxDB or ThingSpeak) is configured.

        :return: The validated Configuration object.
        :raises ValueError: If neither InfluxDB nor ThingSpeak is configured.
        """
        if self.influxdb is None and self.thingspeak is None:
            raise ValueError("At least one of 'influxdb' or 'thingspeak' must be configured")
        return self


def load_configuration_from_file(config_file: Path) -> Configuration:
    """Load and validate configuration from a YAML file.

    :param config_file: Path to the YAML configuration file.
    :return: Validated Configuration object.
    :raises ConfigurationError: If the file is missing, unparseable, or fails validation.
    """
    try:
        with open(config_file) as f:
            raw = yaml.safe_load(f)
        return Configuration.model_validate(raw)
    except FileNotFoundError as e:
        raise ConfigurationError(e) from e
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Failed to parse configuration file: {e}") from e
    except ValidationError as e:
        raise ConfigurationError(f"Configuration validation error:\n{e}") from e
