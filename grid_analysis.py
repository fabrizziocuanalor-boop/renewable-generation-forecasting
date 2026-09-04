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

# Let's look closely at the hours leading up to and around that swing
print("\nZooming in on the hours around the biggest swing (Dec 29, 2023):")
window = midland[
    (midland["timestamp"] >= "2023-12-29 14:00:00") &
    (midland["timestamp"] <= "2023-12-29 20:00:00")
]
print(window[["timestamp", "wind_generation_mwh", "solar_generation_mwh", "combined_generation_mwh"]])

# ============================================
# Isolate "unpredictable" variability: wind swings during daytime hours only
# (excluding solar's predictable sunrise/sunset swings)
# ============================================

midland["hour_of_day"] = midland["timestamp"].dt.hour

# Daytime = roughly 9am to 5pm, when solar is fairly stable/high, not ramping up/down
daytime = midland[(midland["hour_of_day"] >= 9) & (midland["hour_of_day"] <= 17)].copy()
daytime["wind_hour_to_hour_change"] = daytime["wind_generation_mwh"].diff()

# IMPORTANT FIX: filtering to daytime hours creates gaps in the timeline
# (e.g. 5pm one day is immediately followed by 9am the next day in this filtered table).
# .diff() doesn't know about that gap, so it would wrongly compare 5pm to the NEXT
# day's 9am as if they were consecutive hours. We remove those fake "overnight swings"
# by only keeping rows where the actual time gap between rows is exactly 1 hour.
daytime["time_gap"] = daytime["timestamp"].diff()
daytime_clean = daytime[daytime["time_gap"] == pd.Timedelta(hours=1)]

print("\n" + "=" * 50)
print("DAYTIME-ONLY WIND VARIABILITY (excluding sunrise/sunset, and excluding overnight gaps)")
print("=" * 50)
print(daytime_clean["wind_hour_to_hour_change"].describe())

# Compare: how does this stack up against ALL hours' wind swings?
midland["wind_hour_to_hour_change"] = midland["wind_generation_mwh"].diff()
print("\nFor comparison, wind swings across ALL hours:")
print(midland["wind_hour_to_hour_change"].describe())

# Calculate the 95th percentile of wind swings (in either direction) directly from real data
wind_swing_95th = midland["wind_hour_to_hour_change"].abs().quantile(0.95)
print(f"\n95th percentile wind swing (absolute value): {wind_swing_95th:.0f} MWh")
# Compare summer vs winter solar sunset drop-off size
midland["month"] = midland["timestamp"].dt.month
midland["solar_change"] = midland["solar_generation_mwh"].diff()

summer = midland[midland["month"].isin([6, 7, 8])]
winter = midland[midland["month"].isin([12, 1, 2])]

print("\nSummer (Jun-Aug) largest solar hourly drops:")
print(summer["solar_change"].min())

print("\nWinter (Dec-Feb) largest solar hourly drops:")
print(winter["solar_change"].min())
# Compare the TYPICAL (not just extreme) size of solar drops by season
print("\nSummer solar hourly changes - describe:")
print(summer["solar_change"].describe())

print("\nWinter solar hourly changes - describe:")
print(winter["solar_change"].describe())

midland["year"] = midland["timestamp"].dt.year

winter_2021 = midland[(midland["month"].isin([12, 1, 2])) & (midland["year"] == 2021)]
winter_2022 = midland[(midland["month"].isin([12, 1, 2])) & (midland["year"] == 2022)]
winter_2023 = midland[(midland["month"].isin([12, 1, 2])) & (midland["year"] == 2023)]

print("\nWinter 2021 biggest solar drop:", winter_2021["solar_change"].min())
print("Winter 2022 biggest solar drop:", winter_2022["solar_change"].min())
print("Winter 2023 biggest solar drop:", winter_2023["solar_change"].min())