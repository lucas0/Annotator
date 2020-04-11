import pandas as pd
import sys

samples = pd.read_csv("samples.csv", sep="\t")
bad_links = pd.read_csv("bad_links.csv", sep="\t")

print(len(bad_links))

new_bad_link =  sys.argv[1]
samples_line = samples.loc[samples.source_url == new_bad_link]

bad_links = pd.concat([bad_links, samples_line])

bad_links.to_csv("bad_links.csv", index=False, sep="\t")
