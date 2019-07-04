import pandas as pd
import ast
import os,sys
import urllib

cwd = os.path.abspath(__file__+"/..")
data_dir = os.path.abspath(cwd+"/../annotator/data/")
html_dir = data_dir+"/html_snopes"

sources = pd.read_csv(data_dir+"/samples.csv", sep="\t")

invalid_domains = ["facebook, twitter"]

for idx,e in sources.iterrows():
    src_lst = ast.literal_eval(e.source_list)
    new_list = []
    for idx,src in enumerate(src_lst):
        domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urllib.parse.urlparse(src))
        if any(invalid_domains) in domain:
            #remove src from list and delete saved html file
            page_path = e.page.strip("/").split("/")[-1]
            html_filename = html_dir+"/"+page_path+"/"+str(idx)+"html"
            if os.exists(html_filename):
                print(html_filename)
                sys.exit(1)
                os.remove(html_filename)

