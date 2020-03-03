from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.http import JsonResponse
import json
import codecs
import ftfy
import datetime

import os, sys
from os import listdir
from os.path import isfile, join
import pandas as pd
import re

from bs4 import BeautifulSoup as bs
import lxml
import ast

cwd = os.path.abspath(__file__+"/..")
data_dir = os.path.abspath(cwd+"/../data")
html_dir = os.path.abspath(cwd+"/../../html_getter")

res_header = ["page", "claim", "verdict", "tags", "date", "author", "source_list", "source_url", "value", "name"]
op_dict = {'Yes':'1', 'No':'2', 'Invalid Content': '3', "Don't Know": '4'}
save_dict = {'Yes':'yes', 'No':'no', 'Invalid Content': 'ii', "Don't Know": 'dk'}
samples_path = data_dir+"/samples.csv"
results_path = data_dir+"/results/"
snopes_path = data_dir+"/html_snopes/"
count_path = data_dir+"/count.csv"
timelog_path = results_path+"/timelog.txt"
# AUX FUNCTIONS
def guidelines(request):
    return HttpResponseRedirect("https://docs.google.com/document/d/1IkDV9Tscphy_u3Q0cygzfo3SQ8zSWPWt83ynscEw9yo/edit")

def highlight_link(a_html, o_url):
	for a in a_html.find_all("a"):
		if a.has_attr("href"):
			if a["href"] == o_url:
				if a.has_attr("style"):
					s = a["style"]
					if "background-color" in s:
						changed_style = re.sub(r'background-color:.+?(?=[;}])','background-color: yellow',s)
						a["style"] = changed_style
				else:
					a["style"] = "background-color: yellow;"
				break
	return str(a_html)

def get_done_by_annotator(name):
    # creates a list of pages that have been already annotated by the current annotator
    #print("GETTING DONE_BY_ANNOTATOR")
    results_filename = results_path+name+".csv"
    if os.path.exists(results_filename):
        results = pd.read_csv(results_filename, sep=',', encoding="latin1")
        done_by_annotator = results.drop(columns = ["value", "name"])
    else:
        done_by_annotator = pd.DataFrame(columns=res_header).drop(columns = ["value", "name"])
    total_done = len(done_by_annotator)

    return done_by_annotator, total_done

def get_count_file(s_p):
    #Creates or reads countfile
    #print("GETTING COUNT_FILE")
    if os.path.exists(count_path):
        count_file = pd.read_csv(count_path, sep=',', encoding="latin1")
    else:
        count_file = s_p[['page','source_url']].copy()
        count_file['src_len'] = s_p['source_list'].apply(lambda x : len(ast.literal_eval(x)))
        count_file['count'] = 0
        count_file['yes'] = 0
        count_file['no'] = 0
        count_file['ii'] = 0
        count_file['dk'] = 0
        count_file.to_csv(count_path, sep=',', index=False)
    return count_file

def increase_page_annotation_count(page, origin, value):
    count_file = pd.read_csv(count_path, sep=',', encoding="latin1")
    count_file.loc[(count_file['page'] == page) & (count_file['source_url'] == origin),save_dict[value] ]+= 1
    count_file.loc[(count_file['page'] == page) & (count_file['source_url'] == origin), 'count' ]+= 1
    count_file.to_csv(count_path, sep=',', index=False)

def log_annotation(dt,name,value,page,origin):
    with open(timelog_path, "a+") as f:
        d = dt.strftime("%a %d %b, %H:%M:%S")
        msg = (d+"\t"+name+"\t"+value+"\t"+page+"\t"+origin)
        f.write(msg+"\n")

def save_annotation(page, origin, value, name):
    # Read samples file
    print("SAVING ANNOTATION")
    print(">>", name, "|",value,"|", page, "|", origin )
    dt = datetime.datetime.utcnow()
    log_annotation(dt,name,value,page,origin)
    #print("READING S_P")
    s_p = pd.read_csv(samples_path, sep='\t', encoding="latin1")
    entry = s_p.loc[s_p["page"] == page].loc[s_p["source_url"] == origin]
    if not (entry.empty):
        #print("ENTRY EXISTS")
        n_entry = entry.values.tolist()[0]
        n_entry.extend([op_dict[value], name])
        results_filename = results_path+name+".csv"
        results = pd.DataFrame(columns=res_header)
        results.loc[0] = n_entry
        #print("READING RESULTS")
        if os.path.exists(results_filename):
            results.to_csv(results_filename, sep=',', header=False, index=False, mode='a')
        else:
            results.to_csv(results_filename, sep=',', index=False)

        # keeps track of how many times page was annotated
        increase_page_annotation_count(page, origin, value)
    #else:
        #print("ENTRY DOESNT EXIST")

def get_least_annotated_page(name,aPage=None):
    done_by_annotator, total_done = get_done_by_annotator(name)

    #Get bad links
    if os.path.exists(data_dir+"/bad_links.csv"):
        bad_links = (pd.read_csv(data_dir+"/bad_links.csv", sep='\t', encoding="latin1")).drop_duplicates(keep="first")
        res = [done_by_annotator, bad_links]
        after_merge = pd.concat(res)

    #Print number of annotated pages and total number of pages
    s_p = pd.read_csv(samples_path, sep='\t', encoding="latin1").sample(frac=1)
    s_p = s_p.iloc[s_p['source_list'].str.len().argsort()]
    print(">> done: ", len(done_by_annotator), " | total: ", len(s_p))

    if len(after_merge) == len(s_p):
        return "Last annotation done! Thank you!", None, None, None, None, None, None, None, None, None, None

    #Creates or reads countfile:
    count_file = get_count_file(s_p)

    #Get pages not done by current annotator
    not_done_count = (count_file[~(count_file.page.isin(after_merge.page) & count_file.source_url.isin(after_merge.source_url))]).sample(frac=1)
    convert_dict = {'page': str, 'source_url': str, 'src_len': int, 'count': int, 'yes': int, 'no': int, 'ii': int, 'dk': int}
    not_done_count = not_done_count.astype(convert_dict)
    not_done_count.sort_values(by=['src_len'], axis=0 ,ascending=True, inplace=True)

    #print(">>",aPage)
    if aPage is not None:
        remOrigins = not_done_count.loc[not_done_count['page'] == aPage]
        if len(remOrigins)==0:
            return get_least_annotated_page(name)
    else:
        twice_annotated = (not_done_count.loc[not_done_count['count'] == 2])
        once_annotated = (not_done_count.loc[not_done_count['count'] == 1])
        if len(twice_annotated) > 0:
            #print("TWICE")
            yes_annotated = twice_annotated.loc[twice_annotated['yes']!=0]
            if len(yes_annotated) > 0:
                page = yes_annotated.iloc[0]['page']
            else:
                page = twice_annotated.iloc[0]['page']
        else:
            if len(once_annotated) > 0:
                #print("ONCE")
                yes_annotated = once_annotated.loc[once_annotated['yes']!=0]
                if len(yes_annotated) > 0:
                    page = yes_annotated.iloc[0]['page']
                else:
                    page = once_annotated.iloc[0]['page']
            else:
                #print("OTHER")
                index = (not_done_count['count']).idxmin(axis=0, skipna=True)
                page = not_done_count.loc[index]['page']
        remOrigins = not_done_count.loc[not_done_count['page'] == page]

    entry = remOrigins.iloc[0]
    entry = s_p[(s_p.page.isin([entry.page]) & s_p.source_url.isin([entry.source_url]))].iloc[0]
    #modified to be a specific page
    #entry = s_p[s_p.page.isin(["https://www.snopes.com/fact-check/michelle-wolf-hulu-special/"])].iloc[0]

    a_page = entry.page.strip()
    o_page = entry.source_url.strip()
    #print("CHOSEN PAGE | SOURCE", a_page, o_page)
    src_lst = entry.source_list.strip()
    claim_text = (entry.claim).replace("-"," ")
    #To avoid "deformed node" ast error
    try :
        src_lst = ast.literal_eval(src_lst)
    except:
        src_lst = ast.literal_eval(src_lst.decode())

    path_of_both = snopes_path + (a_page.strip("/").split("/")[-1]+"/")

    a_page_path = path_of_both+"page.html"

    src_idx_num = src_lst.index(o_page)
    o_page_path = path_of_both+str(src_idx_num)+".html"

    # If page has a broken link, get another page (instead of looping over all sources)
    if not (os.path.exists(o_page_path) and os.path.exists(a_page_path)):
        if not (os.path.exists(o_page_path)):
            print("SOURCE PATH NOT FOUND")
        if not (os.path.exists(a_page_path)):
            print("PAGE PATH NOT FOUND")
        #save_annotation(a_page, o_page, '3', name)
        return get_least_annotated_page(name)

    f = codecs.open(a_page_path, encoding='utf-8')
    a_html = bs(f.read(),"lxml")

    f = codecs.open(o_page_path, encoding='utf-8')
    o_html = bs(f.read(),"lxml")

    #filenames = [f for f in listdir(path_of_both)]
    a_total = len(ast.literal_eval(entry.source_list))
    a_done  = len(done_by_annotator.loc[done_by_annotator["page"] == a_page])
    #print("PATH FOUND")

    left2 = len(twice_annotated)
    left1 = len(once_annotated)
    return a_page, o_page, a_html, str(o_html), src_lst, a_done, a_total, total_done, claim_text, left2, left1

# VIEWS
def home(request):
	#print("GOT INTO INDEX")
	user = request.user
	session = request.session
	#print(">>", user)
	if not user.is_authenticated:
		print("NOT LOGGED IN")
		return render(request, 'home.html')
	else:
		# return render(request, 'home.html', {'t1':"<html></html>", 't2':"<html></html>", 't3':"asda", 't4':"asdas", 'a_done':0, 'a_total':0, 't_done':0, 'alpha':0})
		#print("USER LOGGED IN")
		name = user.username
		if request.method == 'POST':
			#print("METHOD IS POST")
			op = request.POST.copy().get('op')
			if op:
				op =re.sub('^[^a-zA-z]*|[^a-zA-Z]*$','',op)
                                #print("OPTION:", op)
				if op in list(op_dict.keys()):
					op_item = op_dict[op]
					#print("OPTION NUM", op_item)
					if not ("test" in name):
						save_annotation(session.get('claim'),session.get('origin'), op, name)

					apage = session.get('claim') if op in ["3","2"] else None

					a_url, o_url, a_html, o_html, src_lst, a_done, a_total, t_done, c_text, left2, left1 = get_least_annotated_page(name, apage)
					# Turn string representation of a list to a list
					#print("",a_url,"","",o_url,"","",src_lst,"","")
			else:
				a_url = session.get('claim')
				o_url = session.get('origin')
				a_html = session.get('a_html')
				o_html = session.get('o_html')
				src_lst = session.get('src_lst')
				a_done = session.get('a_done')
				a_total = session.get('a_total')
				t_done = session.get('t_done')
				c_text = session.get('c_text')
		else:
			a_url, o_url, a_html, o_html, src_lst, a_done, a_total, t_done, c_text, left2, left1 = get_least_annotated_page(name)
			# Turn string representation of a list to a list
                        #print("",a_url,"","",o_url,"","",src_lst,"","")

		# Highlight link with scr == source_url
		if a_html:
			if not (type(a_html) == str):
				a_html = highlight_link(a_html, o_url)

		#Save claim and origin links and list of origins in session
		session['claim'] = a_url
		session['origin'] = o_url
		session['a_html'] = a_html
		session['o_html'] = o_html
		session['src_lst'] = src_lst
		session['a_done'] = a_done
		session['a_total'] = a_total
		session['t_done'] = t_done
		session['c_text'] = c_text
		session['left2'] = left2
		session['left1'] = left1

		#Render home page (annotator)
		assert a_html is not None, "A_HTML IS NONE"
		assert o_html is not None, "O_HTML IS NONE"
		assert a_url is not None, "A_URL IS NONE"
		assert o_url is not None, "O_URL IS NONE"
		assert a_done is not None, "A_DONE IS NONE"
		assert a_total is not None, "A_TOTAL IS NONE"
		assert t_done is not None, "T_DONE IS NONE"
		assert c_text is not None, "C_TEXT IS NONE"
		assert left2 is not None, "LEFT2 IS NONE"
		assert left1 is not None, "LEFT1 IS NONE"
		#print("DISPLAYING ARTICLE | SOURCE :", a_url, "|", o_url)
		c_text = ftfy.fix_text(c_text)
		return render(request, 'home.html', {'t1':a_html, 't2':o_html, 't3':a_url, 't4':o_url, 'a_done':a_done, 'a_total':a_total, 't_done':t_done, 'claim':c_text, 'left2':left2, 'left1':left1})

def signup(request):
	if request.method == 'POST':
		form = UserCreationForm(request.POST)
		if form.is_valid():
			user = form.save()
			return redirect('home')
	else:
		form = UserCreationForm();
	return render(request, 'registration/signup.html', {
			'form' : form
		})

def change_origin(request):
	if request.method == 'POST':
		session = request.session

		print("[change_origin]",request.body,"")

		received = json.loads(request.body.decode())

		print("[change_origin]",received,"")

		page = session.get('claim')
		curr_source_url = session.get('origin')
		src_lst = session.get('src_lst')
		clicked_source_url = received['clicked_source']
		try:
			src_idx_num = src_lst.index(clicked_source_url)
		except:
			return JsonResponse({'msg': "bad", 'source': session.get('o_html'), 'n_link':curr_source_url, 'o_link':clicked_source_url})

		#Check if path to source exists (ie valid link)
		if not os.path.exists(snopes_path+(page.strip("/").split("/")[-1]+"/")+str((src_idx_num))+".html"):
			print("BAD LINK (Source HTML was not crawled)")
			return JsonResponse({'msg': "bad", 'source': session.get('o_html'), 'n_link':curr_source_url, 'o_link':clicked_source_url})

		results_filename = results_path+request.user.username+".csv"
		#If new user, then nothing is annotated
		if not os.path.exists(results_filename):
			path_to_new_source = snopes_path+(page.strip("/").split("/")[-1]+"/")+str((src_idx_num))+".html"
			session["origin"] = clicked_source_url
			f = codecs.open(path_to_new_source, encoding='utf-8')
			o_html = bs(f.read(),"lxml")
			session['o_html'] = str(o_html)
			#print("new user")
			return JsonResponse({'msg': "ok", 'source': session.get('o_html'), 'n_link':clicked_source_url, 'o_link':curr_source_url})
		else:
			results = pd.read_csv(results_filename, sep=',', encoding="latin1")
			target_row = results.loc[(results["page"] == page) & (results["source_url"] == clicked_source_url)]
			#Check if page+source are in results (ie already annotated link)
			if len(target_row) != 0:
				#print("already done")
				return JsonResponse({'msg': "done", 'source': session.get('o_html'), 'n_link':curr_source_url, 'o_link':curr_source_url})
			#Means this is an old user who didnt annotate clicked link
			path_to_new_source = snopes_path+(page.strip("/").split("/")[-1]+"/")+str((src_idx_num))+".html"
			session["origin"] = clicked_source_url
			f = codecs.open(path_to_new_source, encoding='utf-8')
			o_html = bs(f.read(),"lxml")
			session['o_html'] = str(o_html)
			#print("old user, not done")
			return JsonResponse({'msg': "ok", 'source': session.get('o_html'), 'n_link':clicked_source_url, 'o_link':curr_source_url})
	else:
		return JsonResponse({'msg': "error", "why" : "dont GET this page, only POST"})
