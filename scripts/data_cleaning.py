import pandas as pd

df = pd.read_csv("data/Clean_Dataset.csv")

# Drop useless column
df = df.drop(columns=["Unnamed: 0"])

# Remove duplicates
df = df.drop_duplicates()

# Strip spaces
for col in df.select_dtypes(include="object").columns:
    df[col] = df[col].str.strip()

df.to_csv("clean_dataset_processed.csv", index=False)

print("Cleaned and saved.")
