from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.nlp_parser import parse_nl_query
from app.flux_builder import build_flux
from app.data_parser import extract_points
from app.summary import compute_summary
from app.sensor import SENSOR_CONFIG
from app.config import GRAFANA_API_KEY, GRAFANA_HOST, INFLUX_DATASOURCE_UID
import requests
import logging

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


        for field in fields:
            if field not in SENSOR_CONFIG:
                continue  # safety guard

            cfg = SENSOR_CONFIG[field]

            # ---------------- Build Flux ----------------
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

            all_points.extend(extract_points(r.json(), field))
            print("ffff",r.json())

        summary = compute_summary(all_points)

        return {
            "query": query,
            "summary": summary,
            "sample_points": all_points,
        }

    except Exception as e:
        logging.exception("Error in /nl-query")
        raise HTTPException(status_code=500, detail=str(e))
