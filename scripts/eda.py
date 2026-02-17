import pandas as pd

bdata = pd.read_csv('data/business.csv')
cdata = pd.read_csv('data/Clean_Dataset.csv')
edata = pd.read_csv('data/economy.csv')

bdf = pd.DataFrame(bdata)
cdf = pd.DataFrame(cdata)
edf = pd.DataFrame(edata)

'''
print("Businnes.csv:\n")
print(bdf.head())
print(bdf.info())
print(bdf.describe())

print("Clean_Dataset.csv:\n")
print(cdf.head())
print(cdf.info())
print(cdf.describe())

print("economy.csv:\n")
print(edf.head())
print(edf.info())
print(edf.describe())
cdf = cdf.drop(columns=["Unnamed: 0"])
'''

print(cdf.duplicated().sum())

print(cdf["airline"].unique())
print(cdf["source_city"].unique())
print(cdf["destination_city"].unique())
print(cdf["class"].unique())