import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

nrel_key = os.getenv("NREL_API_KEY")

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

# Our 4 representative Texas locations
locations = [
    {"name": "midland", "lat": 31.99, "lon": -102.08},
    {"name": "sweetwater", "lat": 32.47, "lon": -100.41},
    {"name": "fortstockton", "lat": 30.89, "lon": -102.88},
    {"name": "amarillo", "lat": 35.22, "lon": -101.83},
]

years = [2021, 2022, 2023]

url = "https://developer.nlr.gov/api/nsrdb/v2/solar/nsrdb-GOES-aggregated-v4-0-0-download.csv"

for location in locations:
    for year in years:
        filename = f"data/raw/weather_{location['name']}_{year}.csv"

        if os.path.exists(filename):
            print(f"Already have {filename}, skipping.")
            continue

        params = {
            "api_key": nrel_key,
            "wkt": f"POINT({location['lon']} {location['lat']})",
            "names": str(year),
            "attributes": "ghi,wind_speed,cloud_type,air_temperature",
            "leap_day": "false",
            "interval": "60",
            "utc": "false",
            "email": "fabrizziocuanalor@gmail.com"
        }

        print(f"Downloading {location['name']}, {year}...")
        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 200:
            with open(filename, "w") as f:
                f.write(response.text)
            print(f"  Saved to {filename}")
        else:
            print(f"  FAILED (status {response.status_code}): {response.text[:200]}")

        time.sleep(1)

print("All downloads complete!")
