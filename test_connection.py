import os
import requests
from dotenv import load_dotenv

# This line reads your .env file and loads the keys into memory
load_dotenv()

# Grab the EIA key from what we just loaded
eia_key = os.getenv("EIA_API_KEY")

print("Did we find an EIA key?", eia_key is not None)

# Try asking the EIA website for a tiny bit of real data
url = "https://api.eia.gov/v2/electricity/rto/fuel-type-data/data/"
params = {
    "frequency": "hourly",
    "data[0]": "value",
    "facets[respondent][]": "ERCO",
    "facets[fueltype][]": "WND",
    "start": "2024-01-01T00",
    "end": "2024-01-01T05",
    "api_key": eia_key
}

response = requests.get(url, params=params)
print("Status code (200 means success):", response.status_code)
print(response.json()) 