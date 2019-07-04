from itertools import groupby
import pandas as pd
import ast
import os,sys
import urllib

cwd = os.path.abspath(__file__+"/..")
data_dir = os.path.abspath(cwd+"/../annotator/data/")
html_dir = data_dir+"/html_snopes"

sources = pd.read_csv(data_dir+"/samples.csv", sep="\t")
sources = pd.read_csv(data_dir+"/samples.csv", sep="\t")

invalid_domains = ["facebook, twitter"]
valid_verdicts = ["true", "false", "legend", "mostly true", "mostly false"]

#verdicts = [s for s in sources.verdict.to_list() if len(s) <100 ]
#results = {value: len(list(freq)) for value, freq in groupby(sorted(verdicts))}
#sorted_results = sorted(results.items(), key=lambda kv: kv[1])
#for k,v in sorted_results:
#        print(k,v)
#sys.exit(1)

print(sources.loc[0])
print(len(sources))
for idx,e in sources.iterrows():
    verdict = e.verdict
    if not any(verdict.startswith(vv) for vv in valid_verdicts):
            #remove src from list and delete saved html file
            sources.drop(idx, inplace=True)
            page_path = e.page.strip("/").split("/")[-1]
            html_filename = html_dir+"/"+page_path+"/"+str(idx)+"html"
            if os.path.exists(html_filename):
                print(html_filename)
                os.remove(html_filename)

sources.index = range(len(sources))
print(len(sources))
