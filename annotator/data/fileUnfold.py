# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 11:04:12 2019

@author: Mohamad
"""

import ast
import os

cwd = os.path.abspath(__file__+"/..")

snopes = open(cwd+"/folded_snopes.csv","r")
output = open(cwd+"/samples.csv","a+")
error_log = open(cwd+"/error_log.csv","a+")

in_header = ["page", "claim", "verdict", "tags", "date", "author","source_list"]
out_header = "page\tclaim\tverdict\ttags\tdate\tauthor\tsource_list\tsource_url\n"

output.write(out_header)
in_data=snopes.readlines()

for i in range(1,len(in_data)):
	try:
		sourceList=ast.literal_eval(in_data[i].split("\t")[6])
		for j in range(0,len(sourceList)):
		output.write(in_data[i].rstrip()+"\t"+sourceList[j]+"\n")
	except:
		error_log.write(in_data[i])	

snopes.close()
output.close()
        
