# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 11:04:12 2019

@author: Mohamad
"""

import ast
import os
import pandas as pd

cwd = os.path.abspath(__file__+"/..")
snopes = pd.read_csv(cwd+"/folded_snopes.csv", sep='\t', encoding="latin1")
output_path = cwd+"/samples.csv"

out_header = ["page", "claim", "verdict", "tags", "date", "author","source_list","source_url"]
count = len(snopes)
is_first = True

for idx, e in snopes.iterrows():
    print("Row ",idx," out of ",count)
    entry = e.values.tolist()
    src_lst = ast.literal_eval(entry[6])
    output = pd.DataFrame(columns=out_header)
    for src in src_lst:
        n_entry = entry + [src]
        output.loc[len(output)] = n_entry

    output.to_csv(output_path, sep='\t', header=is_first, index=False, mode='a')
    is_first = False