from collections import defaultdict
from datetime import datetime
import re

def format_time(ts: str) -> str:
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt.strftime("%B %d, %Y at %I:%M %p UTC")


def split_sentences(text):
    """
    Split text into sentences without breaking decimal numbers.
    Uses regex to handle periods that are not part of numbers.
    """
    if not text:
        return []
    # Match periods that are followed by space and capital letter, or end of string
    sentences = re.split(r'(?<!\d)\.(?:\s+|$)', text)
    return [s.strip() for s in sentences if s.strip()]


def compute_summary(points, reasoning_report=None):
    if not points:
        return "No sensor data available."

    grouped = defaultdict(list)
    for p in points:
        grouped[p['measurement']].append(p)

    summaries = []

    for sensor, vals in grouped.items():

        # ---------------- STATUS SENSOR ----------------
        if sensor == "status":
            latest = sorted(vals, key=lambda x: x["time"])[-1]
            value = latest["value"]

            status_text = value.upper() if isinstance(value, str) else "ONLINE" if int(value) == 1 else "OFFLINE"
            formatted_time = format_time(latest["time"])

            summaries.append(f"• {sensor.capitalize()} - Last reported at {formatted_time} - Status: {status_text}")

            if reasoning_report and sensor in reasoning_report:
                for s in split_sentences(reasoning_report[sensor]):
                    summaries.append(f"  • Insight: {s}.")

        # ---------------- NUMERIC SENSORS ----------------
        else:
            nums = [v['value'] for v in vals if isinstance(v['value'], (int, float))]

            if not nums:
                summaries.append(f"• {sensor.capitalize()} - No readings match your query condition.")
                continue

            avg_val = sum(nums) / len(nums)
            min_val = min(nums)
            max_val = max(nums)

            # Numeric summary
            summaries.append(f"• {sensor.capitalize()} - Average {avg_val:.2f} - Minimum {min_val:.2f} - Maximum {max_val:.2f}")

            # Add reasoning as separate bullets
            if reasoning_report and sensor in reasoning_report:
                for s in split_sentences(reasoning_report[sensor]):
                    summaries.append(f" • Insight: {s}.")

    # Join with newline to preserve bullets
    return "\n".join(summaries)
