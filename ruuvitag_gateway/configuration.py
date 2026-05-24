"""Configuration module for the ruuvitag server application.

Defines the configuration classes and functions to load the configuration from a YAML file.
"""

from dataclasses import dataclass
from pathlib import Path

import jsonschema
import yaml

INFLUXDB_SCHEMA = {
    "type": "object",
    "properties": {
        "host": {"type": "string"},
        "port": {"type": "integer"},
        "database": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "measurement": {"type": "string"},
            },
            "required": ["name", "measurement"],
        },
    },
    "required": ["host", "port", "database"],
}

THINGSPEAK_SCHEMA = {
    "type": "object",
    "properties": {
        "channelId": {"type": "integer"},
        "apiKey": {"type": "string"},
        "fields": {
            "type": "object",
            "patternProperties": {"^[a-zA-Z0-9_]+$": {"type": "integer"}},
            "additionalProperties": False,
        },
    },
    "required": ["channelId", "apiKey", "fields"],
}

RUUVITAG_SCHEMA = {
    "type": "object",
    "properties": {
        "device": {
            "type": "object",
            "properties": {
                "mac": {"type": "string"},
                "name": {"type": "string"},
            },
            "required": ["mac", "name"],
        },
    },
    "required": ["device"],
}

SERVICES_SCHEMA = {
    "type": "object",
    "properties": {
        "database": {"type": "string"},
        "cloud": {"type": "string"},
    },
    "required": ["database", "cloud"],
}

# Compose the top-level schema
CONFIGURATION_SCHEMA = {
    "type": "object",
    "properties": {
        "services": SERVICES_SCHEMA,
        "influxdb": INFLUXDB_SCHEMA,
        "thingspeak": THINGSPEAK_SCHEMA,
        "ruuvitag": RUUVITAG_SCHEMA,
    },
    "required": ["ruuvitag", "services"],
    "anyOf": [{"required": ["influxdb"]}, {"required": ["thingspeak"]}],
}


class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""


@dataclass
class InfluxDBDatabase:
    """Configuration for a single InfluxDB database.

    :param name: The name of the database.
    :param measurement: The measurement name within the database.
    """

    name: str
    measurement: str


@dataclass
class InfluxDBConfiguration:
    """Configuration for InfluxDB connection.

    :param host: The InfluxDB host.
    :param port: The InfluxDB port.
    :param database: The database configuration.
    """

    host: str
    port: int
    database: InfluxDBDatabase


@dataclass
class ThingspeakConfiguration:
    """Configuration for ThingSpeak.

    :param channel_id: The ThingSpeak channel ID.
    :param api_key: The ThingSpeak API key.
    :param fields: A mapping of field names to their respective field numbers.
    """

    channel_id: int
    api_key: str
    fields: dict[str, int]


@dataclass
class RuuviTagDevice:
    """Configuration for a single RuuviTag device.

    :param mac: The MAC address of the RuuviTag.
    :param name: The name of the RuuviTag.
    """

    mac: str
    name: str


@dataclass
class RuuviTagConfiguration:
    """Configuration for the RuuviTag module.

    :param device: The RuuviTag device configuration.
    """

    device: RuuviTagDevice


@dataclass
class ServicesConfiguration:
    """Configuration for service selection.

    :param database: Name of the database service to use.
    :param cloud: Name of the cloud service to use.
    """

    database: str | None = None
    cloud: str | None = None


@dataclass
class Configuration:
    """Top-level configuration.

    :param ruuvitag: RuuviTag configuration object.
    :param services: Services configuration object.
    :param influxdb: InfluxDB configuration object.
    :param thingspeak: ThingSpeak configuration object.
    """

    ruuvitag: RuuviTagConfiguration
    services: ServicesConfiguration | None = None
    influxdb: InfluxDBConfiguration | None = None
    thingspeak: ThingspeakConfiguration | None = None


def load_configuration_from_file(config_file: Path) -> Configuration:
    """Load the configuration from a YAML file and return a Configuration object.

    :param config_file: Path to the YAML configuration file.
    :return: Configuration object with InfluxDB, ThingSpeak, and RuuviTag settings.
    :raises ConfigurationError: If the file is not found or if there are parsing errors.
    """
    try:
        with open(config_file) as f:
            data = yaml.safe_load(f)

        # Validate the configuration against the schema
        try:
            jsonschema.validate(instance=data, schema=CONFIGURATION_SCHEMA)
        except jsonschema.ValidationError as e:
            raise ConfigurationError(
                
                    f"Configuration validation error: {e.message}\n"
                    f"Schema ["
                    f"{'.'.join(map(str, list(e.schema_path)[1:-1]))}]:\n"
                    f"{e.schema}\n"
                    f"Instance:\n{e.instance}"
                
            ) from e

        # Get the influxdb configuration if it exists
        influxdb = None
        if "influxdb" in data:
            influxdb = InfluxDBConfiguration(
                host=data["influxdb"]["host"],
                port=data["influxdb"]["port"],
                database=InfluxDBDatabase(
                    name=data["influxdb"]["database"]["name"],
                    measurement=data["influxdb"]["database"]["measurement"],
                ),
            )

        # Get the thingspeak configuration if it exists
        thingspeak = None
        if "thingspeak" in data:
            thingspeak = ThingspeakConfiguration(
                channel_id=data["thingspeak"]["channelId"],
                api_key=data["thingspeak"]["apiKey"],
                fields=data["thingspeak"]["fields"],
            )

        # Create and return the Configuration object
        return Configuration(
            ruuvitag=RuuviTagConfiguration(
                device=RuuviTagDevice(
                    mac=data["ruuvitag"]["device"]["mac"],
                    name=data["ruuvitag"]["device"]["name"],
                ),
            ),
            services=ServicesConfiguration(
                database=data["services"]["database"],
                cloud=data["services"]["cloud"],
            ),
            influxdb=influxdb,
            thingspeak=thingspeak,
        )
    except FileNotFoundError as e:
        raise ConfigurationError(e) from e
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Failed to parse configuration file: {e}") from e
    except KeyError as e:
        raise ConfigurationError(f"Missing required configuration key: {e}") from e
