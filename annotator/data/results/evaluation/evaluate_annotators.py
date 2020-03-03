import pandas as pd
import re
import os,sys
import numpy as np
import matplotlib.pyplot as plt
import datetime
import seaborn as sns

cwd = os.path.abspath(__file__+"/..")
res_path = os.path.abspath(cwd+"/..")

timedf = pd.read_csv(res_path+"/timelog.txt", sep="\t")
seconds_in_day = 24 * 60 * 60

def conformity(df,concat,binary):
    concat = dict(concat['value'].value_counts(normalize =True))
    name = dict(df['value'].value_counts(normalize =True))
    distance = abs(concat.get(1, 0) - name.get(1, 0))
    if binary:
        return distance
    no_dis = abs(concat.get(2, 0) - name.get(2, 0))
    ic_dis = abs(concat.get(3, 0) - name.get(3, 0))
    #no_distance = abs((concat.get(4, 0) + concat.get(2,0) + concat.get(3,0)) - (name.get(4, 0) + name.get(2,0) + name.get(3, 0)))
    return(distance+(0.5*no_dis)+(0.5*ic_dis))

def distribution(df,concat):
    values = df['value']
    general_values = concat['value']
    binwidth = 1
    bins = range(min(values), max(values) + 2*binwidth, binwidth)
    plt.hist(values, bins = bins, alpha=0.5, label=name, density = True)
    bins = range(min(general_values), max(general_values) + 2*binwidth, binwidth)
    plt.hist(general_values, bins = bins, alpha=0.5, label='Avg', density = True)
    plt.legend(loc='upper right')
    plt.show()

concat = []
#for each annotator
individual = []
individual_sessions = {name.lower():[] for name in timedf.name.unique()}
for res in os.listdir(res_path):
    res_filename = res_path+"/"+res
    if ".csv" in res_filename:
        df = pd.read_csv(res_filename)
        concat.append(df)

        #stats from all sessions
        name = re.sub("\.csv$","",res.lower())
        df.drop_duplicates(subset="source_url", inplace=True)
        individual.append((name,df))

        #generating each session status
        time_annotator = timedf.loc[timedf['name'].str.lower() == name]
        p_datetime = datetime.datetime(1, 1, 1, 0, 0)
        session = []
        check = len(time_annotator)
        for idx,row in time_annotator.iterrows():
            c_datetime = datetime.datetime.strptime(row["date"],"%a %d %b, %H:%M:%S")
            delta = (c_datetime - p_datetime)
            delta_min = ((delta.days * seconds_in_day + delta.seconds) / 60)
            #new session
            if delta_min > 10:
                if len(session) > 0:
                    individual_sessions[name].append(session)
                session = []

            session.append(row)
            p_datetime = c_datetime
            check -= 1
            if check == 0: 
                individual_sessions[name].append(session)

#comprises the concatenation of all the annotations
concat = pd.concat(concat, axis=0)

#get stats for each individual annotator (concatenating all of their respective sessions)
conformities = []
for name,df in individual:
    #if name in ['nell','loredana','lucas','utku']:
    #if name in ['utku']:
    #print(name, conformity(df,concat, True))
    conformities.append((name,conformity(df,concat,True)))
    #distribution(df,concat)

#generate stats per session
msgs = []
for name in individual_sessions.keys():
    for session in individual_sessions[name]:
        first_datetime = datetime.datetime.strptime(session[0]["date"],"%a %d %b, %H:%M:%S").replace(year=2020)
        last_datetime = datetime.datetime.strptime(session[-1]["date"],"%a %d %b, %H:%M:%S").replace(year=2020)
        delta = (last_datetime - first_datetime)
        delta_min = ((delta.days * seconds_in_day + delta.seconds) / 60)
        fdt = first_datetime.strftime("%a %d %b, %H:%M:%S")
        ldt = last_datetime.strftime("%a %d %b, %H:%M:%S")
        min_per_ann = delta_min / len(session)
        session = pd.DataFrame(session)

        #change str for int in session value
        session.loc[session['value'] == 'Yes'] = 1
        session.loc[session['value'] == 'No'] = 2
        session.loc[session['value'] == 'Invalid Content'] = 3
        session.loc[session['value'] == 'I Don\'t Know'] = 4

        session_conformity = conformity(session,concat,True)
        msg = (">>"+ name+" | "+ fdt+"<->"+ldt+ " | total time:"+ "%0.2f mins | "%delta_min+ "\n | "+ "Avg. Speed: %0.2f Min/Ann | "%min_per_ann+"Conformity: %0.2f | "%session_conformity+ "#Ann:"+ str(len(session)))
        msgs.append(msg)

#write the sessionlog.txt
with open("sessionlog.txt", "w+") as f:
    for msg in msgs:
        f.write(msg+"\n\n")

#writes individual_conformities.txt
conformities = sorted(conformities,key=lambda x: x[1])
with open("individual_conformities.txt", "w+") as f:
    for name,score in conformities:
        f.write(name+str(score)+"\n")

#frame = pd.concat(concat, axis=0)
#print(frame.groupby('value').page.count())
#frame.drop_duplicates(subset="source_url", inplace=True)
#print(frame.groupby('value').page.count())

#TODO:
# evaluate annotators per session and save it to a txt
