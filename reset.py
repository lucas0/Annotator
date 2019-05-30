import pandas as pd
import sys,os

filename = sys.argv[0]
cwd = os.path.abspath(filename+"/..")

#set the counters to 0
count = pd.read_csv(cwd+"/data/count.csv")
count['count'] = 0
count.to_csv(cwd+"/data/count.csv", index=False)

results_path = cwd+'/data/results'
for filename in os.listdir(results_path):
    file_path = os.path.join(results_path, filename)
    try:
        if os.path.isfile(file_path):
            os.unlink(file_path)
    except Exception as e:
        print(e)
