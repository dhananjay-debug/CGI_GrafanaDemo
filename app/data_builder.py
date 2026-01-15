# status_builder.py
import time
from datetime import datetime, timezone

ONLINE_THRESHOLD_SECONDS = 300  # 5 minutes

def status_from_timestamp(ts: int) -> dict:
    """
    Convert a Unix timestamp to a readable online/offline status.
    Automatically detects:
    - nanoseconds -> converts to seconds
    - milliseconds -> converts to seconds
    """
    # Convert nanoseconds -> seconds
    if ts > 1e18:  # larger than 1 quintillion -> nanoseconds
        ts = ts / 1e9
    # Convert milliseconds -> seconds
    elif ts > 1e12:  # larger than 1 trillion -> milliseconds
        ts = ts / 1e3

    now = time.time()
    is_online = (now - ts) <= ONLINE_THRESHOLD_SECONDS
    last_seen_dt = datetime.fromtimestamp(ts, tz=timezone.utc)

    # Format as: January 14, 2026, at 1:22 PM UTC
    last_seen_str = last_seen_dt.strftime("%B %d, %Y, at %I:%M %p UTC").replace(" 0", " ")

    return {
        "status": "online" if is_online else "offline",
        "last_seen": last_seen_str
    }

def build_sensor_status_message(sensor_point: dict, updates_count: int = 1) -> str:
    """
    Build a readable status message from a sensor data point.
    sensor_point = {
        "measurement": "status",
        "_value": 1673703753000,  # can be seconds, ms, or ns
        "topic": "sensors/cảm biến nhiệt độ, độ ẩm/status"
    }
    updates_count = number of times the sensor was updated
    """
    # Handle missing or invalid _value
    if "_value" not in sensor_point or sensor_point["_value"] is None:
        return f"No sensor data available for '{sensor_point.get('topic', 'unknown')}'."

    try:
        ts = int(sensor_point["_value"])
    except ValueError:
        return f"Invalid timestamp value for sensor '{sensor_point.get('topic', 'unknown')}'."

    status_info = status_from_timestamp(ts)

    # Proper plural for updates
    update_word = "update" if updates_count == 1 else "updates"

    return (
        f"The sensor '{sensor_point.get('topic', 'unknown')}' status has been updated {updates_count} {update_word}. "
        f"The most recent update shows it was {status_info['status']} on {status_info['last_seen']}."
    )


# Example usage
if __name__ == "__main__":
    raw_point = {
        "measurement": "status",
        "_value": 1673703753000,  # can be seconds, ms, or ns
        "topic": "sensors/cảm biến nhiệt độ, độ ẩm/status"
    }
    print(build_sensor_status_message(raw_point))
