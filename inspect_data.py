import pandas as pd

# Let's look at one weather file first
print("=" * 50)
print("WEATHER FILE")
print("=" * 50)

weather = pd.read_csv("data/raw/weather_midland_2021.csv", skiprows=2)
print("Shape (rows, columns):", weather.shape)
print("\nColumn names:")
print(weather.columns.tolist())
print("\nFirst 5 rows:")
print(weather.head())

# Now let's look at one generation file
print("\n" + "=" * 50)
print("GENERATION FILE")
print("=" * 50)

generation = pd.read_csv("data/raw/generation_WND_2021.csv")
print("Shape (rows, columns):", generation.shape)
print("\nColumn names:")
print(generation.columns.tolist())
print("\nFirst 5 rows:")
print(generation.head())
