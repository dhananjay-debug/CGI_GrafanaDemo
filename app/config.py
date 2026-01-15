import os
from dotenv import load_dotenv
import httpx
from openai import OpenAI

load_dotenv()

GRAFANA_API_KEY = os.getenv("GRAFANA_API_KEY")
GRAFANA_HOST = os.getenv("GRAFANA_HOST")
INFLUX_DATASOURCE_UID = os.getenv("INFLUX_DATASOURCE_UID")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "Factory")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

# OpenAI client
openai_client = None
if OPENAI_API_KEY:
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY, http_client=httpx.Client(verify=False))
    except Exception as e:
        print(f"OpenAI init failed: {e}")
