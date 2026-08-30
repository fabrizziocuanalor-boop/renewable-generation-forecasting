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
train = df[df["year"] < 2023]
test = df[df["year"] == 2023]

print(f"\nTraining set: {train.shape[0]} rows (years 2021-2022)")
print(f"Testing set: {test.shape[0]} rows (year 2023)")

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

# Choose our "inputs" (features) and our "answer" (target) for predicting wind
features = ["Wind Speed", "Temperature", "hour", "month"]
target = "wind_generation_mwh"

X_train = train[features]
y_train = train[target]

X_test = test[features]
y_test = test[target]

# Create and train the model
model = LinearRegression()
model.fit(X_train, y_train)

# Use the trained model to predict on data it's never seen (2023)
predictions = model.predict(X_test)

# Check how good the predictions actually are
mae = mean_absolute_error(y_test, predictions)
r2 = r2_score(y_test, predictions)

print(f"\nWIND MODEL RESULTS")
print(f"Mean Absolute Error: {mae:.0f} MWh")
print(f"R² score: {r2:.3f}")

# Let's also see what the model learned - which features matter most
print(f"\nModel coefficients (how much each feature matters):")
for feature, coef in zip(features, model.coef_):
    print(f"  {feature}: {coef:.2f}")

# ============================================
# Now let's do the same thing for SOLAR
# ============================================

solar_features = ["GHI", "Temperature", "hour", "month"]
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
