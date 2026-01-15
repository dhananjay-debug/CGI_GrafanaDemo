# Sensor → Influx configuration (CORRECT MODEL)
SENSOR_CONFIG = {
    "temperature": {
        "measurement": "sensor_temperature",
        "field": "value",
        "topics": ["sensors/ruuvi/sauna/temperature"]
    },
    "humidity": {
        "measurement": "sensor_temperature",
        "field": "value",
        "topics": ["sensors/ruuvi/sauna/humidity"]
    },
    "battery": {
        "measurement": "sensor_temperature",
        "field": "value",
        "topics": ["sensors/ruuvi/sauna/battery"]
    },
    "light": {
        "measurement": "sensor_light",
        "field": "light",
        "topics": ["sensors/light"]
    },
    "status": {
        "measurement": "sensor_status",
        "field": "status",
        "topics": ["status"]
    }
}


STATUS_MAP = {
    "online": "Online",
    "offline": "Offline"
}
