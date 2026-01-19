from collections import defaultdict
from app.config import openai_client
from datetime import datetime

def format_time(ts: str) -> str:
    """
    Convert ISO timestamp (UTC) to readable format
    e.g. '2026-01-19T08:00:00Z' → 'January 19, 2026 at 08:00 AM UTC'
    """
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt.strftime("%B %d, %Y at %I:%M %p UTC")


def compute_summary(points, reasoning_report=None):
    """
    Build a human-readable summary for sensor points.
    Optional: append reasoning text per field.
    Handles numeric sensors, status sensors, and filtered thresholds.
    """
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

            # Already interpreted (ONLINE / OFFLINE)
            if isinstance(value, str):
                status_text = value.upper()
            else:
                # backward compatibility: numeric status
                status_text = "ONLINE" if int(value) == 1 else "OFFLINE"

            formatted_time = format_time(latest["time"])

            if status_text == "OFFLINE":
                summaries.append(
                    f"The sensor last reported at {formatted_time} and is currently OFFLINE."
                )
            else:
                summaries.append(
                    f"The sensor is currently ONLINE. Last update was at {formatted_time}."
                )

        # ---------------- NUMERIC SENSORS ----------------
        else:
            # Keep only numeric values
            nums = [v['value'] for v in vals if isinstance(v['value'], (int, float))]

            if not nums:
                summaries.append(f"No {sensor} readings available or matched the query condition.")
                continue

            avg_val = sum(nums) / len(nums)
            min_val = min(nums)
            max_val = max(nums)

            summaries.append(
                f"{sensor.capitalize()} → avg {avg_val:.2f}, min {min_val:.2f}, max {max_val:.2f}"
            )

            # Append reasoning if available
            if reasoning_report and sensor in reasoning_report:
                summaries.append(f"{sensor.capitalize()} reasoning: {reasoning_report[sensor]}")

    summary_text = " | ".join(summaries)

    # ---------------- OPTIONAL AI REWRITE ----------------
    if openai_client:
        try:
            ai = openai_client.responses.create(
                model="gpt-4.1-mini",
                input=f"Rewrite this sensor summary in simple language:\n{summary_text}"
            )
            if getattr(ai, "output_text", None):
                summary_text = ai.output_text.strip()
        except Exception:
            pass

    return summary_text
