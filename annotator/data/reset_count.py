import os

cwd = os.path.abspath(__file__+"/..")

os.remove(cwd+"count.csv")

#Get a list of all csv files in input subdirectory
filenames = [f for f in listdir(cwd+"/results") if isfile(join(cwd+"/results", f))]
for file in filenames:
    if file.split(".")[-1] == "csv":
        os.remove(cwd+"/results"+"/"+file)
    else:
        continue
