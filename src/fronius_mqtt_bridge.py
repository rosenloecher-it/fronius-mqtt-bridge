#!/usr/bin/env python3
import logging
import sys
from typing import Optional

import click

from src.app_config import AppConfig
from src.app_logging import AppLogging, LOGGING_CHOICES
from src.fronmod.fronmod_processor import FronmodProcessor
from src.fronmod.fronmod_reader import FronmodReader
from src.mqtt_client import MqttClient
from src.runner import Runner


_logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--json-schema",
    is_flag=True,
    help="Prints the config file JSON schema and exits."
)
@click.option(
    "--config-file",
    default="/etc/froggit-mqtt-logger.yaml",
    help="Config file",
    show_default=True,
    # type=click.Path(exists=True),
)
@click.option(
    "--log-file",
    help="Log file (if stated journal logging is disabled)"
)
@click.option(
    "--log-level",
    help="Log level",
    type=click.Choice(LOGGING_CHOICES, case_sensitive=False),
)
@click.option(
    "--print-logs",
    is_flag=True,
    help="Prints log output to console too"
)
@click.option(
    "--systemd-mode",
    is_flag=True,
    help="Systemd/journald integration: skip timestamp + prints to console"
)
def _main(json_schema, config_file, log_file, log_level, print_logs, systemd_mode):
    try:
        if json_schema:
            AppConfig.print_config_file_json_schema()
        else:
            run_service(config_file, log_file, log_level, print_logs, systemd_mode)

    except KeyboardInterrupt:
        pass

    except Exception as ex:
        _logger.exception(ex)
        sys.exit(1)  # a simple return is not understood by click


def run_service(config_file, log_file, log_level, print_logs, systemd_mode):
    """Logs MQTT messages to a Postgres database."""

    runner = None  # type: Optional[Runner]

    mqtt_client = None  # type: MqttClient
    fronmod_reader = None  # type: FronmodReader
    fronmod_processor = None  # type: FronmodProcessor

    try:
        app_config = AppConfig(config_file)
        AppLogging.configure(
            app_config.get_logging_config(),
            log_file, log_level, print_logs, systemd_mode
        )

        _logger.debug("start")

        runner_config = app_config.get_runner_config()
        mqtt_config = app_config.get_mqtt_config()
        fronmod_config = app_config.get_fronmod_config()

        mqtt_client = MqttClient(mqtt_config)
        fronmod_reader = FronmodReader(fronmod_config)
        fronmod_processor = FronmodProcessor(fronmod_reader)

        runner = Runner(runner_config, mqtt_client, fronmod_processor)
        runner.run()

    finally:
        _logger.info("shutdown")
        if runner is not None:
            runner.close()
        if fronmod_processor is not None:
            fronmod_processor.close()
        if fronmod_reader is not None:
            fronmod_reader.close()
        if mqtt_client is not None:
            mqtt_client.close()


if __name__ == '__main__':
    _main()  # exit codes must be handled by click!
