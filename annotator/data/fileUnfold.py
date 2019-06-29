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

in_header = ["page", "claim", "verdict", "tags", "date", "author","source_list"]
out_header = ["page", "claim", "verdict", "tags", "date", "author","source_list","source_url"]

for idx, e in snopes.iterrows():
    entry = e.values.tolist()
    src_lst = ast.literal_eval(entry[6])
    for src in src_lst:
        n_entry = entry.extend([src])
        if os.path.exists(output_path):
            output = pd.read_csv(output_path, sep='\t', encoding="latin1")
        else:
            output = pd.DataFrame(columns=out_header)
        output.loc[len(output)] = n_entry
        output.to_csv(output_path, sep='\t', index=False)