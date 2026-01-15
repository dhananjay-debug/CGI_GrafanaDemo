# fluxbuilder.py
from app.config import INFLUX_BUCKET
import datetime

def flux_time(dt: datetime.datetime):
    """Convert datetime to RFC3339 format (UTC) for Flux queries."""
    return dt.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_flux(start, end, topics, measurement: str):
    """
    Build a Flux query for InfluxDB.
    
    - start, end: datetime objects
    - topics: list of topic strings
    - measurement: measurement name ("status" or others)
    """
    topic_filter = " or ".join([f'r.topic == "{t}"' for t in topics])

    flux = f"""
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: time(v: "{flux_time(start)}"), stop: time(v: "{flux_time(end)}"))
  |> filter(fn: (r) => ({topic_filter}) and exists r._value)
"""

    if measurement == "status":
        # Convert _value to seconds to simplify downstream processing
        flux += """
  |> last()
  |> map(fn: (r) => ({
      r with
      _value: float(v: r._value) / 1000000000.0  // nanoseconds -> seconds
  }))
"""
    else:
        flux += """
  |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)
"""

    flux += """
  |> keep(columns: ["_time", "_value", "topic"])
"""
    return flux.strip()