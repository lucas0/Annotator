import os, sys
import re
import pandas as pd
import subprocess

cwd = os.path.abspath(__file__+"/..")
data_dir = os.path.abspath(cwd+"/../annotator/data/")
samples_path = data_dir+"/samples.csv"
html_path = data_dir+"/html_snopes/"

samples = pd.read_csv(samples_path, sep='\t', encoding="utf_8")
num_samples = len(samples)

for idx, e in samples.iterrows():
    print("\n|> ROW: ",idx,"/",num_samples)
    a_dir_name = html_path+e.page.strip("/").split("/")[-1]+"/"
    print(a_dir_name)

    if not os.path.exists(a_dir_name):
        os.makedirs(a_dir_name)

    a_html_filename = a_dir_name+"page.html"
    a_new_html_filename = a_dir_name+"page_bck.html"

    cmd = "mv "+a_html_filename+" "+a_new_html_filename

    subprocess.call(cmd, shell=True)
