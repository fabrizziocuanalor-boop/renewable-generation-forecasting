import os
import requests
from dotenv import load_dotenv

load_dotenv()

nrel_key = os.getenv("NREL_API_KEY")

print("Did we find an NREL key?", nrel_key is not None)

url = "https://developer.nlr.gov/api/nsrdb/v2/solar/nsrdb-GOES-aggregated-v4-0-0-download.csv"
params = {
    "api_key": nrel_key,
    "wkt": "POINT(-102.08 31.99)",
    "names": "2022",
    "attributes": "ghi,wind_speed,cloud_type,air_temperature",
    "leap_day": "false",
    "interval": "60",
    "utc": "false",
    "email": "fabrizziocuanalor@gmail.com"
}

# This "headers" part disguises our Python script as a normal web browser,
# so the website's security system doesn't block it
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

response = requests.get(url, params=params, headers=headers)
print("Status code (200 means success):", response.status_code)
print(response.text[:1000])
