import os
import requests
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

# Load credentials
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
COMPANY_ID = os.getenv("COMPANY_ID")
ENVIRONMENT = os.getenv("ENVIRONMENT", "sandbox")
SCOPE = "https://api.businesscentral.dynamics.com/.default"

AUTH_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

# Pydantic model for input and output
class MCPInput(BaseModel):
    context: Dict[str, Any]
    inputs: List[Dict[str, Any]]

class MCPOutput(BaseModel):
    predictions: List[Dict[str, Any]]
    metadata: Dict[str, Any]

def get_token():
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": SCOPE,
    }
    res = requests.post(AUTH_URL, data=payload)
    res.raise_for_status()
    return res.json()["access_token"]

def fetch_customers():
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    url = f"https://api.businesscentral.dynamics.com/v2.0/{TENANT_ID}/{ENVIRONMENT}/ODataV4/Company('{COMPANY_ID}')/customers"
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    return res.json().get("value", [])

@app.post("/predict", response_model=MCPOutput)
async def predict(request: Request):
    mcp_data = await request.json()
    data = MCPInput(**mcp_data)

    # Currently just returns customers; extendable via context
    customers = fetch_customers()

    return MCPOutput(
        predictions=customers,
        metadata={
            "source": "BusinessCentral",
            "type": "customer",
            "count": len(customers)
        }
    )
