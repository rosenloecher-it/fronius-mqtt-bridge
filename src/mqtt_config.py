
class MqttConfKey:
    CLIENT_ID = "client_id"
    HOST = "host"
    PORT = "port"
    PASSWORD = "password"
    USER = "user"
    KEEPALIVE = "keepalive"
    PROTOCOL = "protocol"
    QOS = "qos"
    RETAIN = "retain"

    SSL_CA_CERTS = "ssl_ca_certs"
    SSL_CERTFILE = "ssl_certfile"
    SSL_INSECURE = "ssl_insecure"
    SSL_KEYFILE = "ssl_keyfile"


MQTT_JSONSCHEMA = {
    "type": "object",
    "properties": {
        MqttConfKey.CLIENT_ID: {"type": "string", "minLength": 1},
        MqttConfKey.HOST: {"type": "string", "minLength": 1},
        MqttConfKey.KEEPALIVE: {"type": "integer", "minimum": 1},
        MqttConfKey.PORT: {"type": "integer"},
        MqttConfKey.PROTOCOL: {"type": "integer", "enum": [3, 4, 5]},
        MqttConfKey.SSL_CA_CERTS: {"type": "string", "minLength": 1},
        MqttConfKey.SSL_CERTFILE: {"type": "string", "minLength": 1},
        MqttConfKey.SSL_INSECURE: {"type": "boolean"},
        MqttConfKey.SSL_KEYFILE: {"type": "string", "minLength": 1},
        MqttConfKey.USER: {"type": "string", "minLength": 1},
        MqttConfKey.PASSWORD: {"type": "string"},
        MqttConfKey.QOS: {"type": "integer", "enum": [0, 1, 2]},
        MqttConfKey.RETAIN: {"type": "boolean", "description": "Default: True"},

    },
    "additionalProperties": False,
    "required": [MqttConfKey.HOST],
}
