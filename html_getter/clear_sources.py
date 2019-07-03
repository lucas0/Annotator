import pandas as pd
import ast
import os,sys

cwd = os.path.abspath(__file__+"/..")
data_dir = os.path.abspath(cwd+"/../annotator/data/")

sources = pd.read_csv(data_dir+"/samples.csv", sep="\t")

for idx,e in sources.iterrows():
    src_lst = ast.literal_eval(e.source_list)
    print(src_lst)
    sys.exit(1)
print(len(sources))
