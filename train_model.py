import pandas as pd

# Load our final dataset
df = pd.read_csv("data/final_dataset.csv")

# Fix the timestamp column (remember, saving to CSV turned it back into plain text)
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Add some helpful new columns: what hour of the day, and what month, each row is
# This matters because solar/wind output depends heavily on time of day and season
df["hour"] = df["timestamp"].dt.hour
df["month"] = df["timestamp"].dt.month
df["year"] = df["timestamp"].dt.year

print("Data with new time-based columns:")
print(df[["timestamp", "hour", "month", "year"]].head())

# Split chronologically: train on 2021-2022, test on 2023
train = df[df["year"] < 2023].copy()
test = df[df["year"] == 2023].copy()

print(f"\nTraining set: {train.shape[0]} rows (years 2021-2022)")
print(f"Testing set: {test.shape[0]} rows (year 2023)")

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

# ============================================
# WIND MODEL
# ============================================

# New feature: wind power relates to wind speed CUBED (roughly), not wind speed directly.
# Adding this lets our straight-line model bend to match that real-world curve.
train["wind_speed_cubed"] = train["Wind Speed"] ** 3
test["wind_speed_cubed"] = test["Wind Speed"] ** 3

features = ["Wind Speed", "wind_speed_cubed", "Temperature", "hour", "month"]
target = "wind_generation_mwh"

X_train = train[features]
y_train = train[target]

X_test = test[features]
y_test = test[target]

model = LinearRegression()
model.fit(X_train, y_train)

predictions = model.predict(X_test)

mae = mean_absolute_error(y_test, predictions)
r2 = r2_score(y_test, predictions)

print(f"\nWIND MODEL RESULTS (with wind speed cubed added)")
print(f"Mean Absolute Error: {mae:.0f} MWh")
print(f"R² score: {r2:.3f}")

print(f"\nModel coefficients (how much each feature matters):")
for feature, coef in zip(features, model.coef_):
    print(f"  {feature}: {coef:.2f}")

# ============================================
# SOLAR MODEL
# ============================================

solar_features = ["GHI", "Cloud Type", "Temperature", "hour", "month"]
solar_target = "solar_generation_mwh"

X_train_solar = train[solar_features]
y_train_solar = train[solar_target]

X_test_solar = test[solar_features]
y_test_solar = test[solar_target]

solar_model = LinearRegression()
solar_model.fit(X_train_solar, y_train_solar)

solar_predictions = solar_model.predict(X_test_solar)

solar_mae = mean_absolute_error(y_test_solar, solar_predictions)
solar_r2 = r2_score(y_test_solar, solar_predictions)

print(f"\nSOLAR MODEL RESULTS")
print(f"Mean Absolute Error: {solar_mae:.0f} MWh")
print(f"R² score: {solar_r2:.3f}")

print(f"\nModel coefficients (how much each feature matters):")
for feature, coef in zip(solar_features, solar_model.coef_):
    print(f"  {feature}: {coef:.2f}")

# ============================================
# Chart: Actual vs Predicted solar generation, sample week
# ============================================

import matplotlib.pyplot as plt

sample_week = test[(test["timestamp"] >= "2023-06-01") & (test["timestamp"] <= "2023-06-07")].copy()
sample_week_features = sample_week[solar_features]
sample_week_predictions = solar_model.predict(sample_week_features)

plt.figure(figsize=(12, 5))
plt.plot(sample_week["timestamp"], sample_week["solar_generation_mwh"], label="Actual", linewidth=2)
plt.plot(sample_week["timestamp"], sample_week_predictions, label="Predicted", linewidth=2, linestyle="--")
plt.xlabel("Date")
plt.ylabel("Solar Generation (MWh)")
plt.title("Solar Generation: Actual vs. Predicted (Sample Week, June 2023)")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("solar_prediction_chart.png", dpi=150)
print("\nChart saved to solar_prediction_chart.png")

# ============================================
# VIF check: formally confirming the multicollinearity we found manually
# ============================================

from statsmodels.stats.outliers_influence import variance_inflation_factor

vif_data = train[solar_features].copy()

print("\n" + "=" * 50)
print("VIF CHECK (solar model features)")
print("A VIF above ~5-10 signals real multicollinearity")
print("=" * 50)

for i, feature in enumerate(solar_features):
    vif_value = variance_inflation_factor(vif_data.values, i)
    print(f"  {feature}: VIF = {vif_value:.2f}")\

    import matplotlib.pyplot as plt

plt.figure(figsize=(8, 5))
plt.scatter(train["hour"], train["GHI"], alpha=0.1, s=5)
plt.xlabel("Hour of Day")
plt.ylabel("GHI (Sunlight)")
plt.title("GHI vs Hour of Day (checking for a non-linear relationship)")
plt.savefig("ghi_vs_hour_check.png", dpi=150)
print("Saved ghi_vs_hour_check.png")
    