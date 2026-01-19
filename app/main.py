from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.nlp_parser import parse_nl_query
from app.flux_builder import build_flux
from app.data_parser import extract_points
from app.summary import compute_summary
from app.sensor import SENSOR_CONFIG, STATUS_MAP
from app.config import GRAFANA_API_KEY, GRAFANA_HOST, INFLUX_DATASOURCE_UID
import requests
import logging
from datetime import datetime

app = FastAPI(title="Agentic Smart Factory API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/ping")
def ping():
    return {"pong": True}


@app.get("/")
def root():
    return {"status": "Smart Factory API running"}


@app.post("/nl-query")
def nl_query(req: dict):
    try:
        query = req.get("query", "")

        # ---------------- Parse NL query ----------------
        start, end, fields, tags = parse_nl_query(query)

        all_points = []
        reasoning_report = {}

        for field in fields:
            if field not in SENSOR_CONFIG:
                continue

            cfg = SENSOR_CONFIG[field]

            flux = build_flux(
                start=start,
                end=end,
                topics=cfg.get("topics"),
                measurement=cfg["measurement"]
            )

            payload = {
                "queries": [
                    {
                        "refId": "A",
                        "datasource": {
                            "type": "influxdb",
                            "uid": INFLUX_DATASOURCE_UID
                        },
                        "queryType": "flux",
                        "rawQuery": True,
                        "query": flux
                    }
                ]
            }

            r = requests.post(
                f"https://{GRAFANA_HOST}/api/ds/query",
                headers={
                    "Authorization": f"Bearer {GRAFANA_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
                verify=False,
                timeout=15,
                proxies={"http": None, "https": None},
            )

            points = extract_points(r.json(), field)
            all_points.extend(points)

            # ---------------- Compute stats ----------------
            values = [p.get("value") for p in points if p.get("value") is not None]

            # --- Handle status sensors separately ---
            if cfg["measurement"] == "sensor_status":
                stats = {"min_value": None, "max_value": None, "avg_value": None, "count": len(values)}
            else:
                # Convert numeric values safely
                numeric_values = []
                for v in values:
                    try:
                        numeric_values.append(float(v))
                    except (TypeError, ValueError):
                        continue

                stats = {
                    "min_value": min(numeric_values) if numeric_values else None,
                    "max_value": max(numeric_values) if numeric_values else None,
                    "avg_value": sum(numeric_values) / len(numeric_values) if numeric_values else None,
                    "count": len(numeric_values)
                }

            # ---------------- Reasoning ----------------
            reasoning_cfg = cfg.get("reasoning", {})
            reasoning_parts = []

            # --- Status sensors reasoning ---
            if cfg["measurement"] == "sensor_status":
                if values:
                    last_val = values[-1].lower()
                    last_time = points[-1]["time"] if points else None
                    formatted_time = last_time
                    if last_time:
                        dt = datetime.fromisoformat(last_time.replace("Z", "+00:00"))
                        formatted_time = dt.strftime("%B %d, %Y at %I:%M %p UTC")

                    status_text = STATUS_MAP.get(last_val, last_val.upper())
                    reasoning_parts.append(
                        f"The sensor last sent a report on {formatted_time} and is now {status_text}."
                    )
                else:
                    if reasoning_cfg.get("check_missing", False):
                        reasoning_parts.append(f"No status data recorded for '{field}' yesterday.")

            # --- Numeric sensors reasoning ---
            else:
                if stats["count"] == 0 and reasoning_cfg.get("check_missing", False):
                    reasoning_parts.append(f"No data recorded for '{field}' yesterday.")
                else:
                    # Check constant readings
                    if reasoning_cfg.get("check_constant", False) and stats["min_value"] == stats["max_value"]:
                        reasoning_parts.append(
                            f"Sensor value constant at {stats['min_value']:.2f}; may indicate a malfunction or lack of change."
                        )

                    # Trend/consistency comment
                    if len(values) > 1:
                        delta = max(numeric_values) - min(numeric_values)
                        if delta < 0.1 * abs(stats['avg_value'] or 1):
                            reasoning_parts.append(
                                "The readings show minimal fluctuation, indicating stable measurements."
                            )

                    # Human-readable stats with unit and last timestamp
                    unit = cfg.get("unit", "")
                    last_time = points[-1]["time"] if points else None
                    formatted_time = last_time
                    if last_time:
                        dt = datetime.fromisoformat(last_time.replace("Z", "+00:00"))
                        formatted_time = dt.strftime("%B %d, %Y at %I:%M %p UTC")

                    reasoning_parts.append(
                        f"{field.capitalize()} readings as of {formatted_time}: "
                        f"average {stats['avg_value']:.2f}{unit}, "
                        f"low {stats['min_value']:.2f}{unit}, "
                        f"high {stats['max_value']:.2f}{unit}."
                    )

                    # Check against expected range
                    expected = reasoning_cfg.get("expected_range")
                    if expected and stats["min_value"] is not None:
                        if stats["min_value"] < expected[0] or stats["max_value"] > expected[1]:
                            reasoning_parts.append(
                                f"These readings are outside the expected range ({expected[0]}–{expected[1]})."
                            )
                        else:
                            reasoning_parts.append(
                                f"These readings are within the expected operational range ({expected[0]}–{expected[1]})."
                            )

            reasoning_report[field] = " ".join(reasoning_parts)

        # ---------------- Inject reasoning into sample points ----------------
        for p in all_points:
            field = p.get("field")
            if field in reasoning_report:
                p["reasoning"] = reasoning_report[field]

        # ---------------- Compute summary ----------------
        summary = compute_summary(all_points, reasoning_report=reasoning_report)
        for field, text in reasoning_report.items():
            summary += f"\n{field} reasoning: {text}"

        # ---------------- Return JSON ----------------
        return {
            "query": query,
            "summary": summary,
            "sample_points": all_points,
            "reasoning": reasoning_report
        }

    except Exception as e:
        logging.exception("Error in /nl-query")
        raise HTTPException(status_code=500, detail=str(e))
