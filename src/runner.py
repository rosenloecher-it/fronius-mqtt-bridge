import asyncio
import copy
import datetime
import logging
import signal
import threading
from asyncio import Task
from collections import namedtuple
from typing import Dict, Optional

from src.fronmod.fronmod_config import FronmodDelivery, FronmodConfig
from src.fronmod.fronmod_processor import FronmodProcessor
from src.fronmod.mobu import MobuFlag
from src.mqtt_client import MqttClient
from src.runner_config import RunnerConfKey
from src.utils.time_utils import TimeUtils

_logger = logging.getLogger(__name__)


class RunnerDelivery:

    def __init__(self, delivery: FronmodDelivery, period: float, topic: str):

        self.delivery = delivery
        self.period = period
        self.topic = topic

        self.next_trigger = TimeUtils.now()

    def retrigger(self):
        self.next_trigger = TimeUtils.now() + datetime.timedelta(seconds=self.period)


RunnerResult = namedtuple('RunnerResult', ['topic', 'values'])


class Runner:

    DEFAULT_DELIVERY_TIME_QUICK = 10
    DEFAULT_DELIVERY_TIME_MEDIUM = 60
    DEFAULT_DELIVERY_TIME_SLOW = 300
    DEFAULT_FETCH_TIMEOUT = 10

    ROUND_FLOAT = 7

    JSON_STATUS = "status"
    JSON_TIMESTAMP = "timestamp"

    TIME_LIMIT_MQTT_CONNECTION = 10  # seconds

    def __init__(self, config: dict, mqtt_client: MqttClient, fronmod_processor: FronmodProcessor):
        # config
        self._fetch_timeout = config.get(RunnerConfKey.FETCH_TIMEOUT, self.DEFAULT_FETCH_TIMEOUT)
        self._last_will_message = config.get(RunnerConfKey.MESSAGE_LAST_WILL)

        self._hide_items = set(config.get(RunnerConfKey.HIDE_ITEMS, []))

        tick_time = config.get(RunnerConfKey.DELIVERY_TIME_QUICK, self.DEFAULT_DELIVERY_TIME_QUICK) / FronmodConfig.TICK_COUNTER

        self._quick_delivery = RunnerDelivery(
            delivery=FronmodDelivery.QUICK,
            period=tick_time,  # used as tick time, there will be delivered after full cycle
            topic=config.get(RunnerConfKey.TOPIC_QUICK),
        )
        self._medium_delivery = RunnerDelivery(
            delivery=FronmodDelivery.QUICK,
            period=config.get(RunnerConfKey.DELIVERY_TIME_MEDIUM, self.DEFAULT_DELIVERY_TIME_MEDIUM),
            topic=config.get(RunnerConfKey.TOPIC_MEDIUM),
        )
        self._slow_delivery = RunnerDelivery(
            delivery=FronmodDelivery.QUICK,
            period=config.get(RunnerConfKey.DELIVERY_TIME_SLOW, self.DEFAULT_DELIVERY_TIME_SLOW),
            topic=config.get(RunnerConfKey.TOPIC_SLOW),
        )
        self._deliveries = [self._quick_delivery, self._medium_delivery, self._slow_delivery]

        # init
        self._mqtt_client = mqtt_client
        self._fronmod_processor = fronmod_processor

        self._loop = asyncio.get_event_loop()
        self._periodic_task = None  # type: Optional[Task]
        # stretch the requests
        self._tick_task = None  # type: Optional[Task]
        self._tick_started = None  # type: Optional[datetime.datetime]
        self._tick_operation = 0

        self._error_count_fetch_too_long = 0

        if threading.current_thread() is threading.main_thread():
            # integration tests may run the service in a thread...
            signal.signal(signal.SIGINT, self._shutdown_signaled)
            signal.signal(signal.SIGTERM, self._shutdown_signaled)

    def _init_mqtt_client(self):
        if self._last_will_message:
            for delivery in self._deliveries:
                if delivery.topic:
                    self._mqtt_client.set_last_will(delivery.topic, self._last_will_message)

        self._mqtt_client.connect()

    def _shutdown_signaled(self, sig, _frame):
        _logger.info("shutdown signaled (%s)", sig)
        if self._periodic_task:
            self._periodic_task.cancel()

    def run(self):
        """endless loop"""

        self._init_mqtt_client()
        self._fronmod_processor.open()

        self._periodic_task = self._loop.create_task(self._periodic())

        try:
            self._loop.run_until_complete(self._periodic_task)
        except asyncio.CancelledError:
            _logger.debug("canceling...")
        finally:
            self.close()

    async def _wait_for_mqtt_connection_timeout(self, timeout):
        try:
            return await asyncio.wait_for(self._wait_for_mqtt_connection(), timeout)
        except asyncio.exceptions.TimeoutError:
            raise asyncio.exceptions.TimeoutError(f"couldn't connect to MQTT (within {timeout}s)!") from None

    async def _wait_for_mqtt_connection(self):
        while True:
            if self._mqtt_client.is_connected():
                break

            await asyncio.sleep(0.1)

    async def _periodic(self):
        await self._wait_for_mqtt_connection_timeout(self.TIME_LIMIT_MQTT_CONNECTION)

        while True:
            if TimeUtils.now() >= self._quick_delivery.next_trigger:
                self._run_next_tick()
            else:
                self._mqtt_client.ensure_connection()

            await asyncio.sleep(0.1)

    def _run_next_tick(self):
        """the goal of all this magic is to stretch the requests."""
        if self._tick_task:
            if not self._tick_task.done():
                return  # task not done, wait for next loop
            self._handle_results()
        assert self._tick_task is None

        task = None
        if self._tick_operation == 0:
            task = self._process_tick_0
        elif self._tick_operation == 1:
            task = self._process_tick_1
        elif self._tick_operation == 2:
            task = self._process_tick_2
        elif self._tick_operation == 3:
            task = self._process_tick_3
        elif self._tick_operation == 4:
            task = self._process_tick_4

        assert 4 == FronmodConfig.TICK_COUNTER

        if task:
            self._tick_task = self._loop.create_task(self._process_tick_timeout(task))  # type: Task
            self._tick_started = TimeUtils.now()

        self._quick_delivery.retrigger()

        self._tick_operation += 1
        if self._tick_operation > FronmodConfig.TICK_COUNTER:
            self._tick_operation = 0

    async def _process_tick_timeout(self, tick_func, timeout=None):
        timeout = timeout or self._fetch_timeout
        try:
            self._tick_started = TimeUtils.now()
            return await asyncio.wait_for(tick_func(), timeout)
        except asyncio.exceptions.TimeoutError:
            raise asyncio.exceptions.TimeoutError("timeout ({:.1f}s) - abort!".format(timeout))

    async def _process_tick_0(self):
        self._fronmod_processor.process_inverter_model()  # must be first
        # no return value

    async def _process_tick_1(self):
        # depends on _process_tick_0
        self._fronmod_processor.process_mppt_model()
        # no return value

    async def _process_tick_2(self):
        # depends on _process_tick_1
        self._fronmod_processor.process_meter_model()
        values = self._fronmod_processor.get_send_data(MobuFlag.Q_QUICK)
        # values = {"values": "quick"}
        return RunnerResult(topic=self._quick_delivery.topic, values=values)

    async def _process_tick_3(self):
        now = TimeUtils.now()
        if now < self._medium_delivery.next_trigger:
            return
        self._medium_delivery.retrigger()

        values = self._fronmod_processor.get_send_data(MobuFlag.Q_MEDIUM)
        # values = {"values": "medium......"}
        return RunnerResult(topic=self._medium_delivery.topic, values=values)

    async def _process_tick_4(self):
        now = TimeUtils.now()
        if now < self._slow_delivery.next_trigger:
            return
        self._slow_delivery.retrigger()

        self._fronmod_processor.process_storage_model()
        values = self._fronmod_processor.get_send_data(MobuFlag.Q_SLOW)
        # values = {"values": "slow................."}
        return RunnerResult(topic=self._slow_delivery.topic, values=values)

    def _sent_failure(self):
        values = {
            self.JSON_STATUS: "error",
            self.JSON_TIMESTAMP: TimeUtils.now(True).isoformat()
        }

        for delivery in self._deliveries:
            self._mqtt_client.publish(topic=delivery.topic, payload=values)

    def _handle_results(self):
        if not self._tick_task or not self._tick_task.done():
            return

        try:
            result = self._tick_task.result()  # may raise exception from task
            self._tick_task.cancel()
            task_time_used = (TimeUtils.now() - self._tick_started).total_seconds()
        except Exception:
            self._sent_failure()
            raise
        finally:
            self._tick_task = None
            self._tick_started = None

        if task_time_used >= self._quick_delivery.period + 0.5:  # as task get checked at concrete time intervals
            self._error_count_fetch_too_long += 1
            if self._error_count_fetch_too_long < 50:
                _logger.warning(
                    "fetching data took too long - wrong timing (?): duration=%.1fs; max-expected=%.1fs (quick-time / %d); timeout=%.1fs",
                    task_time_used, self._quick_delivery.period, FronmodConfig.TICK_COUNTER, self._fetch_timeout,
                )
            elif self._error_count_fetch_too_long % 50 == 0:
                _logger.warning("fetching data took too long - too many errors. these errors are now disabled!")

        if not result:
            return
        if not result.values:
            return

        values = Runner.round_floats(result.values)

        if not values.get(self.JSON_TIMESTAMP):
            values[self.JSON_TIMESTAMP] = TimeUtils.now(True).isoformat()
        if not values.get(self.JSON_STATUS):
            values[self.JSON_STATUS] = "ok"

        for hide_item in self._hide_items:
            values.pop(hide_item, None)

        self._mqtt_client.publish(topic=result.topic, payload=values)

    def close(self):
        if self._mqtt_client is not None:
            try:
                if self._last_will_message:
                    for delivery in self._deliveries:
                        if delivery.topic:
                            self._mqtt_client.publish(topic=delivery.topic, payload=self._last_will_message)
            except Exception as ex:
                _logger.error("could not publish the final service messages! %s", ex)

            self._mqtt_client = None

    @classmethod
    def round_floats(cls, values: Dict[str, any]) -> Dict[str, any]:
        if values is None:
            return values

        values = copy.deepcopy(values)

        for key, value in values.items():
            if isinstance(value, float):
                values[key] = round(value, cls.ROUND_FLOAT)

        return values
