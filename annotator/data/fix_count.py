import pandas as pd
import os, sys
import ast

cwd = os.path.abspath(__file__+"/..")
count_filename = cwd+"/count.csv"
samples_filename = cwd+"/samples.csv"
results_path = cwd+"/results/"

samples = pd.read_csv(samples_filename, sep='\t')
new_count = []
new_header = ['page', 'source_url', 'src_len', 'count', 'yes','no','ii','dk']

def get_count(source, page):
    yes = no = ii = dk = 0
    for filename in os.listdir(results_path):
        res = pd.read_csv(results_path+filename)
        match = res.loc[res.page == page].loc[res.source_url == source]
        if len(match) > 0:
            v = match.iloc[0].value
            if v == 1:
                yes += 1
            if v == 2:
                yes += 1
            if v == 3:
                ii += 1
            if v == 4:
                dk += 1

    return yes, no, ii, dk, (yes+no+ii+dk)

for i,e in samples.iterrows():
    entry = [e.page, e.source_url]
    src_len = len(ast.literal_eval(e.source_list))
    yes, no, ii, dk, count = get_count(e.source_url, e.page)
    entry = entry+[src_len,count,yes,no,ii,dk]
    print(i)
    new_count.append(entry)

new_count_df = pd.DataFrame(new_count)
new_count_df.to_csv(cwd+"/new_count.csv", header=new_header, index=False)

