import pandas as pd

df = pd.read_csv("data/final_dataset.csv")
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Focus on one location to avoid double-counting ERCOT's system-wide generation numbers
midland = df[df["location"] == "midland"].copy()
midland = midland.sort_values("timestamp")

# Combined renewable generation = wind + solar together
midland["combined_generation_mwh"] = midland["wind_generation_mwh"] + midland["solar_generation_mwh"]

# Hour-to-hour change: how much did generation swing from one hour to the next?
midland["hour_to_hour_change"] = midland["combined_generation_mwh"].diff()

print("Combined generation statistics:")
print(midland["combined_generation_mwh"].describe())

print("\nHour-to-hour SWING statistics (the key grid preparedness number):")
print(midland["hour_to_hour_change"].describe())

# The single biggest hour-to-hour swing in the whole 3-year dataset
biggest_swing_idx = midland["hour_to_hour_change"].abs().idxmax()
biggest_swing_row = midland.loc[biggest_swing_idx]
print(f"\nBiggest single hour-to-hour swing:")
print(f"  Timestamp: {biggest_swing_row['timestamp']}")
print(f"  Swing size: {biggest_swing_row['hour_to_hour_change']:.0f} MWh")

# Let's look closely at the hours right around that suspicious midnight swing
print("\nZooming in on the hours around Dec 29-30, 2023:")
window = midland[
    (midland["timestamp"] >= "2023-12-29 20:00:00") &
    (midland["timestamp"] <= "2023-12-30 04:00:00")
]
print(window[["timestamp", "wind_generation_mwh", "solar_generation_mwh", "combined_generation_mwh"]])

# Testing the timezone hypothesis: if we shift generation timestamps back by 6 hours,
# does the solar pattern suddenly make physical sense?

test_shift = midland.copy()
test_shift["shifted_timestamp"] = test_shift["timestamp"] - pd.Timedelta(hours=6)

print("\nOriginal vs shifted timestamp, for the suspicious window:")
check = test_shift[
    (test_shift["timestamp"] >= "2023-12-29 18:00:00") &
    (test_shift["timestamp"] <= "2023-12-30 02:00:00")
]
print(check[["timestamp", "shifted_timestamp", "solar_generation_mwh"]])
