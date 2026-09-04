import pandas as pd

# ============================================
# STEP 1: Combine all generation files into one table
# ============================================

years = [2021, 2022, 2023]

wind_pieces = []
solar_pieces = []

for year in years:
    wind_pieces.append(pd.read_csv(f"data/raw/generation_WND_{year}.csv"))
    solar_pieces.append(pd.read_csv(f"data/raw/generation_SUN_{year}.csv"))

wind_all = pd.concat(wind_pieces, ignore_index=True)
solar_all = pd.concat(solar_pieces, ignore_index=True)

# IMPORTANT FIX: EIA's "period" timestamps are in UTC, but our weather data
# is in Texas local time (CST = UTC-6 in winter). We subtract 6 hours here
# so both datasets describe the same real-world moment in time.
wind_all["timestamp"] = pd.to_datetime(wind_all["period"], format="%Y-%m-%dT%H") - pd.Timedelta(hours=6)
solar_all["timestamp"] = pd.to_datetime(solar_all["period"], format="%Y-%m-%dT%H") - pd.Timedelta(hours=6)

wind_all = wind_all[["timestamp", "value"]].rename(columns={"value": "wind_generation_mwh"})
solar_all = solar_all[["timestamp", "value"]].rename(columns={"value": "solar_generation_mwh"})

# Combine wind and solar into one generation table
generation = pd.merge(wind_all, solar_all, on="timestamp", how="inner")

print(f"Combined generation table: {generation.shape[0]} rows")

# ============================================
# STEP 2: For each location, combine its years of weather, then merge with generation
# ============================================

locations = ["midland", "sweetwater", "fortstockton", "amarillo", "abilene", "lubbock", "bigspring", "mccamey"]

all_location_pieces = []

for location in locations:
    weather_pieces = []
    for year in years:
        df = pd.read_csv(f"data/raw/weather_{location}_{year}.csv", skiprows=2)
        weather_pieces.append(df)

    weather = pd.concat(weather_pieces, ignore_index=True)
    weather["timestamp"] = pd.to_datetime(weather[["Year", "Month", "Day", "Hour"]])

    weather = weather[["timestamp", "GHI", "Wind Speed", "Cloud Type", "Temperature"]]

    # Merge this location's weather with the (system-wide) generation data
    merged = pd.merge(weather, generation, on="timestamp", how="inner")

    # Tag every row with which location it came from
    merged["location"] = location

    print(f"  {location}: {merged.shape[0]} rows merged")
    all_location_pieces.append(merged)

# ============================================
# STEP 3: Stack all 4 locations into one final dataset
# ============================================

final_dataset = pd.concat(all_location_pieces, ignore_index=True)

print(f"\nFinal dataset shape: {final_dataset.shape}")
print(final_dataset.head())

# Save it
final_dataset.to_csv("data/final_dataset.csv", index=False)
print("\nSaved to data/final_dataset.csv")
