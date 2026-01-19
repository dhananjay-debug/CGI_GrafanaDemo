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

        # ---------------- Parse NL query ----------------
        start, end, fields, tags = parse_nl_query(query)

        all_points = []
        reasoning_report = {}

        # ---------------- Process each sensor ----------------
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
            numeric_values = []
            filtered_points = []

            if cfg["measurement"] != "sensor_status":
                # identify threshold conditions from query
                matches = re.findall(r"(below|under|less than|above|over|greater than)\s*(-?\d+\.?\d*)", query.lower())
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
            else:
                # For status, keep all points as is
                numeric_values = []

            all_points.extend(points)

            # ---------------- Compute stats ----------------
            if cfg["measurement"] == "sensor_status":
                stats = {"min_value": None, "max_value": None, "avg_value": None, "count": len(points)}
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
                    reasoning_parts.append(f"No status data recorded for '{field}' yesterday.")
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
                            f"Sensor value constant at {stats['min_value']:.2f}; may indicate a malfunction or lack of change."
                        )
                    if stats["count"] > 1 and len(numeric_values) > 1:
                        delta = stats["max_value"] - stats["min_value"]
                        if delta < 0.1 * abs(stats['avg_value'] or 1):
                            reasoning_parts.append(
                                "The readings show minimal fluctuation, indicating stable measurements."
                            )

                    unit = cfg.get("unit", "")
                    reasoning_parts.append(
                        f"The {field} was usually around {stats['avg_value']:.2f}{unit}, "
                        f"going as low as {stats['min_value']:.2f}{unit} and as high as {stats['max_value']:.2f}{unit}."
                    )

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

        return {
            "query": query,
            "summary": summary,
            "sample_points": all_points,
            "reasoning": reasoning_report
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logging.exception("Error in /nl-query")
        raise HTTPException(status_code=500, detail=str(e))
