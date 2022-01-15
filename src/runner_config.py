from src.fronmod.fronmod_config import FronmodConfig, FronmodDelivery


class RunnerConfKey:

    DELIVERY_TIME_QUICK = "delivery_time_quick"
    DELIVERY_TIME_MEDIUM = "delivery_time_medium"
    DELIVERY_TIME_SLOW = "delivery_time_slow"
    FETCH_TIMEOUT = "fetch_timeout"

    MESSAGE_LAST_WILL = "message_last_will"
    TOPIC_QUICK = "topic_quick"
    TOPIC_MEDIUM = "topic_medium"
    TOPIC_SLOW = "topic_slow"

    HIDE_ITEMS = "hide_items"


RUNNER_JSONSCHEMA = {
    "type": "object",
    "properties": {

        RunnerConfKey.FETCH_TIMEOUT: {
            "type": "number",
            "minimum": 2,
            "description": "Timeout to fetch data (seconds)."
        },

        RunnerConfKey.DELIVERY_TIME_QUICK: {
            "type": "number",
            "minimum": 6,
            "description": "Timeout to fetch data (seconds)."
        },
        RunnerConfKey.DELIVERY_TIME_MEDIUM: {
            "type": "number",
            "minimum": 30,
            "description": "Timeout to fetch data (seconds)."
        },
        RunnerConfKey.DELIVERY_TIME_SLOW: {
            "type": "number",
            "minimum": 60,
            "description": "Timeout to fetch data (seconds)."
        },

        RunnerConfKey.MESSAGE_LAST_WILL: {
            "type": "string",
            "minLength": 1,
            "description": "Payload (data) last will (leave empty to not set a las will)."
        },
        RunnerConfKey.TOPIC_QUICK: {
            "type": "string",
            "minLength": 1,
            "description": "Topic for items: " + FronmodConfig.list_items(FronmodDelivery.QUICK)
        },
        RunnerConfKey.TOPIC_MEDIUM: {
            "type": "string",
            "minLength": 1,
            "description": "Topic for items: " + FronmodConfig.list_items(FronmodDelivery.MEDIUM)
        },
        RunnerConfKey.TOPIC_SLOW: {
            "type": "string",
            "minLength": 1,
            "description": "Topic for items: " + FronmodConfig.list_items(FronmodDelivery.SLOW)
        },

    },
    "additionalProperties": False,
    "required": [],
}
