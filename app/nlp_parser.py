import datetime
from app.sensor import SENSOR_TOPIC_MAP

def parse_nl_query(query: str):
    q = query.lower()
    now = datetime.datetime.utcnow()

    # Time detection
    if "yesterday" in q:
        start = (now - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0)
        end = start + datetime.timedelta(days=1)
    else:
        start = now - datetime.timedelta(days=2)
        end = now

    # Sensor detection
    fields = [k for k in SENSOR_TOPIC_MAP if k in q]

    return start, end, fields
