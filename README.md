# # Smart Factory PoC_2- Agentic AI-Chatbot

## Overview
This Proof of Concept (PoC) demonstrates a conversational, AI-driven monitoring system for Smart Factory IoT sensors. It essentially acts like a digital assistant for smart factory monitoring.
It combines:
- **FastAPI** – orchestrates workflows and serves API endpoints.
- **Agentic AI (OpenAI LLM)** – translates numeric sensor data into human-readable insights.
- **NLP queries** – users can ask questions about temperature, humidity, battery, light, and sensor status.
- **Grafana** – visualization interface for sensor data.
- **InfluxDB** – time-series database storing sensor metrics.
It shows how Agentic AI interprets raw sensor data, NLP understands user queries, and FastAPI orchestrates requests to Grafana and InfluxDB. Together, they create a conversational, actionable interface for smart factory monitoring — providing insights, alerts, and historical trends in real time.


Note: While sensor data is stored in InfluxDB, the PoC focuses on providing **human-readable summaries via OpenAI LLM** and fetching them through Grafana to avoid security issues.

---

## Features / Demo Queries

- Show temperature humidity and battery level for yesterday
- What’s the status of sensors yesterday
- Average temperature yesterday
- Maximum temperature last 2 days
- Maximum and minimum humidity last 2 days
- Battery level today
- Battery and status last 1 days
- Give me the battery levels for the last 1 days
- Who is Elon Musk?
---

## Project Structure
Smart-Factory-POC/
│
├── app/
│ ├── init.py
│ ├── main.py # FastAPI entrypoint
│ ├── config.py # Grafana/Influx config
│ ├── nlp_parser.py # NLP query parsing
│ ├── flux_builder.py # Flux query builder for InfluxDB
│ ├── data_parser.py # Parsing raw sensor data
│ ├── summary.py # Summary computation
│ ├── sensor.py # Sensor metadata
│
│
├── venv/ # Python virtual environment (not committed)
├── requirements.txt # Project dependencies
├── .gitignore # Files/folders to ignore in git
└── README.md # This documentation


---

## Setup Instructions

1. Clone the repository
2. Install dependencies
3. Set environment variables
4. Run FastAPI server
5. Access the API
- Open browser: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
6. Run Frontend


# # Agentic AI Explanation # #

This PoC is Agentic AI:

- Autonomous Reasoning: The AI interprets sensor data, detects trends, and decides what to summarize.

- Task Planning: Converts natural language queries into actionable data requests.

- Human-Readable Output: Summarizes raw numeric data into clear insights.

- Integration: Communicates with FastAPI backend and Grafana/InfluxDB for live sensor data.

Workflow Diagram
      ┌──────────────┐
      │  User Query  │
      │ --           │
      └─────┬────────┘
            │
            ▼
 ┌───────────────────────┐
 │      FastAPI API      │
 │   (/nl-query endpoint)│
 └────────┬──────────────┘
          │
          ▼
 ┌───────────────────────┐
 │   Flux Query Builder   │
 │ Builds Grafana Flux    │
 │ queries for measurements│
 └────────┬──────────────┘
          │
          ▼
 ┌───────────────────────┐
 │  Grafana / InfluxDB   │
 │  Returns sensor data  │
 └────────┬──────────────┘
          │ 
          ▼
 ┌───────────────────────┐
 │     Agentic AI        │
 │  (OpenAI LLM GPT-4.1)│
 │ Summarizes sensor data│
 └────────┬──────────────┘
          │
          ▼
 ┌───────────────────────┐
 │   Response to User    │
 │ JSON: summary + points│
 └───────────────────────┘

