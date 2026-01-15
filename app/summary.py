from collections import defaultdict
from app.sensor import STATUS_MAP
from app.config import openai_client

def compute_summary(points):
    if not points:
        return "No sensor data available."

    grouped = defaultdict(list)
    for p in points:
        grouped[p['measurement']].append(p)

    summaries = []

    for sensor, vals in grouped.items():
        if sensor == "status":
            latest = sorted(vals, key=lambda x: x["time"])[-1]
            status_text = STATUS_MAP.get(int(latest['value']), str(int(latest['value'])))
            summaries.append(
                f"Status updated {len(vals)} times. Latest: {status_text} at {latest['time']}."
            )
        else:
            nums = [v['value'] for v in vals]
            summaries.append(
                f"{sensor.capitalize()} → avg {sum(nums)/len(nums):.2f}, min {min(nums):.2f}, max {max(nums):.2f}"
            )

    summary_text = " | ".join(summaries)

    # Optional: AI rewrite
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