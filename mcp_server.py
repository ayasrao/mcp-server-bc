import os  
import requests  
from fastapi import FastAPI, Request  
from pydantic import BaseModel  
from typing import List, Dict, Any  
from dotenv import load_dotenv  
  
load_dotenv()  
  
TENANT_ID = os.getenv("TENANT_ID")  
CLIENT_ID = os.getenv("CLIENT_ID")  
CLIENT_SECRET = os.getenv("CLIENT_SECRET")  
COMPANY_ID = os.getenv("COMPANY_ID")  # Optional  
ENVIRONMENT = os.getenv("ENVIRONMENT", "sandbox")  # "booster", "sandbox", or "production"  
SCOPE = "https://api.businesscentral.dynamics.com/.default"  
AUTH_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"  
  
app = FastAPI()  
  
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
        "Content-Type": "application/json",  
    }  
    url = f"https://api.businesscentral.dynamics.com/v2.0/{TENANT_ID}/{ENVIRONMENT}/api/v2.0/companies"  
    res = requests.get(url, headers=headers)  
    res.raise_for_status()  
    companies = res.json().get("value", [])  
    if not companies:  
        raise Exception("No companies found in this Business Central environment!")  
    company_id = COMPANY_ID or companies[0]["id"]  
    cust_url = f"https://api.businesscentral.dynamics.com/v2.0/{TENANT_ID}/{ENVIRONMENT}/api/v2.0/companies/{company_id}/customers"  
    res = requests.get(cust_url, headers=headers)  
    res.raise_for_status()  
    return res.json().get("value", [])  
@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/predict", response_model=MCPOutput)  
async def predict(request: Request):  
    # Accepts any JSON MCPInput, returns the customer list as "predictions"  
    customers = fetch_customers()  
    return MCPOutput(  
        predictions=customers,  
        metadata={  
            "source": "BusinessCentral",  
            "type": "customer",  
            "count": len(customers)  
        }  
    )
if __name__ == "__main__":
    try:
        customers = fetch_customers()
        print(f"✅ Retrieved {len(customers)} customers.")
        for cust in customers[:5]:
            print(f"- {cust.get('displayName') or cust.get('name')} (ID: {cust.get('id')})")
    except Exception as e:
        print("❌ Error:", e)
