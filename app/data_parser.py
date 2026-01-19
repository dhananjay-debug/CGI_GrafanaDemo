import datetime
import time

OFFLINE_THRESHOLD_SECONDS = 10 * 60  # 10 minutes


def status_from_timestamp(ts: int) -> str:
    now = int(time.time())
    if (now - ts) <= OFFLINE_THRESHOLD_SECONDS:
        return "ONLINE"
    return "OFFLINE"


def extract_points(resp, measurement):
    points = []

    for r in resp.get("results", {}).values():
        for frame in r.get("frames", []):
            fields = frame.get("schema", {}).get("fields", [])
            values = frame.get("data", {}).get("values", [])

            if not fields or not values:
                continue

            time_idx = next(
                (i for i, f in enumerate(fields) if f.get("name") in ["Time", "time"]),
                None
            )
            value_idx = next(
                (i for i, f in enumerate(fields) if f.get("name") in ["Value", "_value"]),
                None
            )

            if time_idx is None or value_idx is None:
                continue

            topic = fields[value_idx].get("labels", {}).get("topic", "")

            for i in range(len(values[time_idx])):
                ts = values[time_idx][i]
                val = values[value_idx][i]

                if val is None:
                    continue

                # Convert Grafana time to ISO
                if isinstance(ts, (int, float)):
                    ts = datetime.datetime.utcfromtimestamp(ts / 1000).isoformat() + "Z"

                # ---------------- STATUS LOGIC ----------------
                if measurement in ["status", "sensor_status"]:
                    status_text = status_from_timestamp(int(val))
                    print("status",status_text)

                    points.append({
                        "time": ts,
                        "value": status_text,
                        "measurement": "status",
                        "field": "status",
                        "topic": topic
                    })

                # ---------------- NUMERIC SENSORS ----------------
                else:
                    points.append({
                        "time": ts,
                        "value": float(val),
                        "measurement": measurement,
                        "field": measurement,
                        "topic": topic
                    })

    return points
