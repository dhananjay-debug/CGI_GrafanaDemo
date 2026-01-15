# Sensor → Influx/Grafana topics
SENSOR_TOPIC_MAP = {
    "temperature": ["sensors/ruuvi/sauna/temperature"],
    "humidity": ["sensors/ruuvi/sauna/humidity"],
    "battery": ["sensors/ruuvi/sauna/battery"],
    "light": ["sensors/ruuvi/sauna/light"],
    "status": ["sensors/cảm biến nhiệt độ, độ ẩm/status"],
}

# Status code mapping
STATUS_MAP = {
    1760930418: "online",
    0: "offline",
    # add more codes if needed
}
