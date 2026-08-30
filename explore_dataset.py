import pandas as pd

df = pd.read_csv("data/final_dataset.csv")

print("Shape:", df.shape)
print("\nColumn names and data types:")
print(df.dtypes)

print("\nAny missing values?")
print(df.isnull().sum())

print("\nBasic statistics:")
print(df.describe())
