import pandas as pd
import os,sys

cwd = os.path.abspath(__file__+"/..")
results_path = cwd+"/results/"

li = []

for res in os.listdir(results_path):
    if ".csv" in res:
        print(results_path+res)
        df = pd.read_csv(results_path+res)
        li.append(df)

frame = pd.concat(li, axis=0)
print("count of all annotations per label")
print(frame.groupby('value').page.count())

print("count of all annotations per label (dropped duplicated source_url)")
frame.drop_duplicates(subset="source_url", inplace=True)
print(frame.groupby('value').page.count())
