import datetime
import re
from app.sensor import SENSOR_CONFIG

def parse_nl_query(query: str):
    import datetime
    import re
    from app.sensor import SENSOR_CONFIG

    q = query.lower()
    now = datetime.datetime.utcnow()

    # ---------------- Time detection ----------------
    start = now - datetime.timedelta(days=2)
    end = now
    if "today" in q:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif "yesterday" in q:
        start = (now - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + datetime.timedelta(days=1)
    m = re.search(r"last (\d+) (hour|day|week)s?", q)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        if unit == "hour":
            start = now - datetime.timedelta(hours=n)
        elif unit == "day":
            start = now - datetime.timedelta(days=n)
        elif unit == "week":
            start = now - datetime.timedelta(weeks=n)

    # ---------------- Sensor detection ----------------
    fields = [k for k in SENSOR_CONFIG if k in q]
    if "status" in q and "status" not in fields:
        fields.append("status")

    # ---------------- Device detection ----------------
    device_match = re.search(r"from device (\w+)", q)
    tags = {"device": device_match.group(1)} if device_match else {}

    # Ensure only 4 values returned
    return start, end, fields, tags
