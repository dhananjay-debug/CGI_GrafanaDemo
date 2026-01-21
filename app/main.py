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
import re

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

            # ---------------- Filter points based on query condition ----------------
            filtered_points = []
            numeric_values = []

            if cfg["measurement"] != "sensor_status":
                matches = re.findall(
                    r"(below|under|less than|above|over|greater than)\s*(-?\d+\.?\d*)",
                    query.lower()
                )
                for p in points:
                    val = p.get("value")
                    try:
                        val_float = float(val)
                    except (TypeError, ValueError):
                        continue

                    keep = True
                    for comparator, threshold in matches:
                        threshold = float(threshold)
                        if comparator in ["below", "under", "less than"]:
                            if val_float >= threshold:
                                keep = False
                        elif comparator in ["above", "over", "greater than"]:
                            if val_float <= threshold:
                                keep = False

                    if keep:
                        filtered_points.append(p)
                        numeric_values.append(val_float)
                points = filtered_points

            all_points.extend(points)

            # ---------------- Compute stats ----------------
            if cfg["measurement"] == "sensor_status":
                stats = {
                    "min_value": None,
                    "max_value": None,
                    "avg_value": None,
                    "count": len(points)
                }
            else:
                stats = {
                    "min_value": min(numeric_values) if numeric_values else None,
                    "max_value": max(numeric_values) if numeric_values else None,
                    "avg_value": sum(numeric_values) / len(numeric_values) if numeric_values else None,
                    "count": len(numeric_values)
                }

            # ---------------- Reasoning ----------------
            reasoning_cfg = cfg.get("reasoning", {})
            reasoning_parts = []

            if cfg["measurement"] == "sensor_status":
                if not points and reasoning_cfg.get("check_missing", False):
                    reasoning_parts.append(f"No status data recorded for '{field}'.")
                elif points:
                    last_val = str(points[-1].get("value")).lower()
                    reasoning_parts.append(
                        f"The sensor is currently {STATUS_MAP.get(last_val, last_val.upper())}."
                    )
            else:
                if stats["count"] == 0:
                    reasoning_parts.append(f"No {field} readings match your query condition.")
                else:
                    if reasoning_cfg.get("check_constant", False) and stats["min_value"] == stats["max_value"]:
                        reasoning_parts.append(
                            f"Sensor value constant at {stats['min_value']:.2f}; may indicate a malfunction."
                        )

                    if stats["count"] > 1 and len(numeric_values) > 1:
                        delta = stats["max_value"] - stats["min_value"]
                        if delta < 0.1 * abs(stats['avg_value'] or 1):
                            reasoning_parts.append(
                                "Readings show minimal fluctuation, indicating stable measurements."
                            )

                    unit = cfg.get("unit", "")
                    reasoning_parts.append(
                        f"Readings around {stats['avg_value']:.2f}{unit}, range {stats['min_value']:.2f}–{stats['max_value']:.2f}{unit}."
                    )

                    expected = reasoning_cfg.get("expected_range")
                    if expected and stats["min_value"] is not None:
                        if stats["min_value"] < expected[0] or stats["max_value"] > expected[1]:
                            reasoning_parts.append(
                                f"Outside expected range ({expected[0]}–{expected[1]})."
                            )
                        else:
                            reasoning_parts.append(
                                f"Within expected operational range ({expected[0]}–{expected[1]})."
                            )

            reasoning_report[field] = " ".join(reasoning_parts)

        # ---------------- Inject reasoning into points ----------------
        for p in all_points:
            field = p.get("field")
            if field in reasoning_report:
                p["reasoning"] = reasoning_report[field]

        # ---------------- Compute bullet-style summary ----------------
        summary = compute_summary(all_points, reasoning_report=reasoning_report)

        # Remove sample points entirely if none match threshold
        points_to_return = [p for p in all_points if p.get("value") is not None]

        return {
            "query": query,
            "summary": summary,
            "sample_points": points_to_return,
            "reasoning": reasoning_report
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logging.exception("Error in /nl-query")
        raise HTTPException(status_code=500, detail=str(e))
