import pandas as pd

# Load one weather file
weather = pd.read_csv("data/raw/weather_midland_2021.csv", skiprows=2)

# Build a single timestamp column by combining Year, Month, Day, Hour
weather["timestamp"] = pd.to_datetime(
    weather[["Year", "Month", "Day", "Hour"]]
)

print("Weather data with new timestamp column:")
print(weather[["timestamp", "GHI", "Wind Speed", "Temperature"]].head(10))

# Load one generation file
generation = pd.read_csv("data/raw/generation_WND_2021.csv")

# The 'period' column looks like "2021-01-01T00" - convert it to a real timestamp too
generation["timestamp"] = pd.to_datetime(generation["period"], format="%Y-%m-%dT%H")

print("\nGeneration data with new timestamp column:")
print(generation[["timestamp", "value"]].head(10))

# Merge the two tables together, matching rows by their timestamp
merged = pd.merge(
    weather[["timestamp", "GHI", "Wind Speed", "Temperature", "Cloud Type"]],
    generation[["timestamp", "value"]],
    on="timestamp",
    how="inner"
)

merged = merged.rename(columns={"value": "wind_generation_mwh"})

print("\nMERGED DATA:")
print(merged.head(10))
print("\nShape of merged data:", merged.shape)
