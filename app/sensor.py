# Sensor → Influx configuration with reasoning
SENSOR_CONFIG = {
    "temperature": {
        "measurement": "sensor_temperature",  # keep as-is
        "field": "value",
        "topics": ["sensors/ruuvi/sauna/temperature"],
        "unit": "°C",
        "reasoning": {
            "expected_range": [20, 25],  # operational range in °C
            "check_missing": True,
            "check_constant": True
        }
    },
    "humidity": {
        "measurement": "sensor_temperature",  # keep as-is
        "field": "value",
        "topics": ["sensors/ruuvi/sauna/humidity"],
        "unit": "%",
        "reasoning": {
            "expected_range": [30, 70],  # operational range in %
            "check_missing": True,
            "check_constant": True
        }
    },
    "battery": {
        "measurement": "sensor_temperature",  # keep as-is
        "field": "value",
        "topics": ["sensors/ruuvi/sauna/battery"],
        "unit": "V",
        "reasoning": {
            "expected_range": [2.5, 3.3],  # typical battery voltage
            "check_missing": True,
            "check_constant": False
        }
    },
    "light": {
        "measurement": "sensor_light",
        "field": "light",
        "topics": ["sensors/light"],
        "unit": "lux",
        "reasoning": {
            "expected_range": [0, 1000],  # lux or ADC
            "check_missing": True,
            "check_constant": True
        }
    },
    "status": {
        "measurement": "status",
        "field": "status",
        "topics": ["sensors/cảm biến nhiệt độ, độ ẩm/status"],
        "unit": " ",
        "reasoning": {
            "expected_values": ["online", "offline"],
            "check_missing": True
        }
    }
}

# Optional human-readable status mapping
STATUS_MAP = {
    "online": "Online",
    "offline": "Offline"
}
