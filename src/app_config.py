import json
import os

import yaml
from jsonschema import validate

from src.app_logging import LOGGING_JSONSCHEMA
from src.fronmod.fronmod_config import FRONMOD_JSONSCHEMA
from src.mqtt_config import MQTT_JSONSCHEMA
from src.runner_config import RUNNER_JSONSCHEMA


CONFIG_JSONSCHEMA = {
    "type": "object",
    "properties": {
        "logging": LOGGING_JSONSCHEMA,
        "modbus": FRONMOD_JSONSCHEMA,
        "mqtt": MQTT_JSONSCHEMA,
        "runner": RUNNER_JSONSCHEMA,
    },
    "additionalProperties": False,
    "required": ["modbus", "mqtt", "runner"],
}


class AppConfig:

    def __init__(self, config_file):
        self._config_data = {}

        self.check_config_file_access(config_file)

        with open(config_file, 'r') as stream:
            file_data = yaml.unsafe_load(stream)

        self._config_data = {
            **{"database": {}, "logging": {}, "mqtt": {}},  # default
            **file_data
        }

        validate(file_data, CONFIG_JSONSCHEMA)

    def get_logging_config(self):
        return self._config_data["logging"]

    def get_fronmod_config(self):
        return self._config_data["modbus"]

    def get_mqtt_config(self):
        return self._config_data["mqtt"]

    def get_runner_config(self):
        return self._config_data["runner"]

    @classmethod
    def check_config_file_access(cls, config_file):
        if not os.path.isfile(config_file):
            raise FileNotFoundError('config file ({}) does not exist!'.format(config_file))

        permissions = oct(os.stat(config_file).st_mode & 0o777)[2:]
        if permissions != "600":
            extra = "change via 'chmod'. this config file may contain sensitive information."
            raise PermissionError(f"wrong config file permissions ({config_file}: expected 600, got {permissions})! {extra}")

    @classmethod
    def print_config_file_json_schema(cls):
        print(json.dumps(CONFIG_JSONSCHEMA, indent=4, sort_keys=True))
