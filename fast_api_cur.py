import json
from fastapi import FastAPI, HTTPException

app = FastAPI()

# Path to your local JSON file
DATA_FILE = "rates.json"

def load_rates():
    """Helper function to load data from the JSON file."""
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

@app.get("/rate/{base_currency}/{target_currency}")
async def get_cross_rate(base_currency: str, target_currency: str):
    """Returns the cross rate for a given currency pair."""
    
    # Normalize inputs to uppercase
    base = base_currency.upper()
    target = target_currency.upper()
    
    data = load_rates()
    
    # Check if base currency exists
    if base not in data:
        raise HTTPException(status_code=404, detail=f"Base currency '{base}' not found.")
    
    # Check if target currency exists for that base
    rate = data[base].get(target)
    
    if rate is None:
        raise HTTPException(status_code=404, detail=f"Rate for {base} to {target} not available.")

    return {
        "base": base,
        "target": target,
        "rate": rate
    }