import numpy as np
import pandas as pd
import os, sys

cwd = os.path.abspath(__file__+"/..")
res_dir = cwd+"/results/"
df_list = []
kappa = []
filenames = os.listdir(res_dir)
#filenames_original = os.listdir(res_dir)
#for name in filenames_original:

    #print(">>>",name)
    #filenames = filenames_original.copy()
    #filenames.remove(name)

for filename in filenames:
    newdf = pd.read_csv(res_dir+filename)
    newdf.drop_duplicates(subset="source_url",inplace=True, keep="first")
    df_list.append(newdf)

#print("total of annotators:", len(df_list))
data = pd.concat(df_list)
#print("total of annotations:", len(data))
copy = data.copy()
copy.drop_duplicates(inplace=True, keep="first", subset="source_url")
#print("total of unique annotated sources:", len(copy))

gold = []
count3 = 0
countNo= 0
lenlen = []
count_array = np.empty((0,4), dtype='float')
b_array = np.empty((0,2), dtype='float')


for i,e in copy.iterrows():
    match = data[data['source_url'] == e['source_url']]
## THIS SHOULD BE CHANGED TO > 3 ONCE MORE ANNOTATIONS ARE MADE
    lenlen.append(len(match))
    if len(match) >0:
        count3 = count3+1
        count = [0,0,0,0]
        b_count = [0,0]
        for i2,e2 in match.iterrows():
            v = e2["value"]
            count[v-1] = count[v-1]+ 1
            if v == 0:
                b_count[0] += 1
            else:
                b_count[1] += 1
        a = np.array(count)
        count_array = np.vstack((count_array,a))
        idx = np.argmax(a)
        if idx == 0:
            gold.append(e)
        if idx == 1:
            countNo = countNo + 1

        b = np.array(b_count)
        b_array = np.vstack((b_array,b))


gold_df = pd.DataFrame(gold)

count = pd.read_csv(cwd+"/count.csv")
matrix = pd.DataFrame(count['source_url'])
for fn in filenames:
    mod_filenames = filenames.copy()
    mod_filenames.remove(fn)
    print(fn, mod_filenames)
    for i,filename in enumerate(mod_filenames):
        newdf = pd.read_csv(res_dir+filename)
        newdf.drop_duplicates(subset="source_url",inplace=True, keep="first")
        matrix["a"+str(i)] = "<NA>"
        for e in newdf.iterrows():
            matrix.loc[matrix['source_url'] == e[1]['source_url'],"a"+str(i)] = e[1]['value']
    matrix2 = matrix.drop(columns=['source_url'])
    matrix2.to_csv(cwd+'/interUserCSVs/interuserMatrixWithout'+fn, index=False)
sys.exit(1)

#end def
#print(len(copy))
#print("more than 3",count3)
#print("more than3 and NO",countNo)
#print("gold size:",len(gold_df))
#gold_df.to_csv(cwd+"/datasetVeritas3.csv", index=False)

#print("average number of annotations per doc:", sum(lenlen)/len(lenlen))
lenlen.sort(reverse = True)
#print(lenlen[:200])
#print(max(lenlen))
#print("NEW")
#print(count_array.shape)
#print(b_array.shape)
print(count_array)
sys.exit(1)
