import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

eia_key = os.getenv("EIA_API_KEY")

fuel_types = ["WND", "SUN"]
years = [2021, 2022, 2023]

url = "https://api.eia.gov/v2/electricity/rto/fuel-type-data/data/"

for fuel in fuel_types:
    for year in years:
        filename = f"data/raw/generation_{fuel}_{year}.csv"

        if os.path.exists(filename):
            print(f"Already have {filename}, skipping.")
            continue

        print(f"Downloading {fuel} generation for {year}...")

        all_records = []
        offset = 0
        page_size = 5000

        # Keep asking for more pages until we get back fewer than a full page
        # (that's the signal that we've reached the end of the data)
        while True:
            params = {
                "frequency": "hourly",
                "data[0]": "value",
                "facets[respondent][]": "ERCO",
                "facets[fueltype][]": fuel,
                "start": f"{year}-01-01T00",
                "end": f"{year}-12-31T23",
                "sort[0][column]": "period",
                "sort[0][direction]": "asc",
                "offset": str(offset),
                "length": str(page_size),
                "api_key": eia_key
            }

            response = requests.get(url, params=params)

            if response.status_code != 200:
                print(f"  FAILED (status {response.status_code}): {response.text[:200]}")
                break

            data = response.json()
            records = data["response"]["data"]
            all_records.extend(records)

            print(f"  Got {len(records)} rows (total so far: {len(all_records)})")

            # If we got back less than a full page, we've reached the end
            if len(records) < page_size:
                break

            offset += page_size
            time.sleep(1)  # be polite between pages too

        # Save everything we collected across all pages
        with open(filename, "w") as f:
            f.write("period,respondent,fueltype,value\n")
            for row in all_records:
                f.write(f"{row['period']},{row['respondent']},{row['fueltype']},{row['value']}\n")

        print(f"  Saved {len(all_records)} total rows to {filename}")
        time.sleep(1)

print("All generation downloads complete!")
