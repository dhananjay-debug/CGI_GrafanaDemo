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


def compute_summary(points):
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
            print("gggg",value)

            # ✅ Already interpreted (ONLINE / OFFLINE)
            if isinstance(value, str):
                status_text = value
            else:
                # backward compatibility
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
            nums = [v['value'] for v in vals if isinstance(v['value'], (int, float))]
            if not nums:
                continue

            summaries.append(
                f"{sensor.capitalize()} → "
                f"avg {sum(nums)/len(nums):.2f}, "
                f"min {min(nums):.2f}, "
                f"max {max(nums):.2f}"
            )

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
