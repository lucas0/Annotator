from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.http import JsonResponse
import json
import codecs

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
op_dict = {'Yes':'1', 'No':'2', 'Invalid Input': '3', "Don't Know": '4'}
samples_path = data_dir+"/samples.csv"
results_path = data_dir+"/results/"
snopes_path = data_dir+"/html_snopes/"
count_path = data_dir+"/count.csv"
# AUX FUNCTIONS

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
    print("GETTING DONE_BY_ANNOTATOR")
    results_filename = results_path+name+".csv"
    if os.path.exists(results_filename):
        results = pd.read_csv(results_filename, sep=',', encoding="latin1")
        done_by_annotator = results.drop(columns = ["value", "name"])
    else:
        done_by_annotator = pd.DataFrame(columns=res_header).drop(columns = ["value", "name"])
    total_done = len(done_by_annotator)
    #Get bad links
    if os.path.exists(data_dir+"/bad_links.csv"):
        bad_links = (pd.read_csv(data_dir+"/bad_links.csv", sep='\t', encoding="latin1")).drop_duplicates(keep="first")
        res = [done_by_annotator, bad_links]
        done_by_annotator = pd.concat(res)

    return done_by_annotator, total_done

def get_count_file(s_p):
    #Creates or reads countfile
    print("GETTING COUNT_FILE")
    if os.path.exists(count_path):
        count_file = pd.read_csv(count_path, sep=',', encoding="latin1")
    else:
        count_file = s_p[['page','source_url']].copy()
        count_file['count'] = 0
        count_file.to_csv(count_path, sep=',', index=False)
    return count_file

def increase_page_annotation_count(page, origin):
    count_file = pd.read_csv(count_path, sep=',', encoding="latin1")
    count_file.loc[(count_file['page'] == page) & (count_file['source_url'] == origin), 'count'] += 1
    count_file.to_csv(count_path, sep=',', index=False)

def save_annotation(page, origin, value, name):
    # Read samples file
    print("SAVING ANNOTATION")
    print("READING S_P")
    s_p = pd.read_csv(samples_path, sep='\t', encoding="latin1")
    entry = s_p.loc[s_p["page"] == page].loc[s_p["source_url"] == origin]
    if not (entry.empty):
        print("ENTRY EXISTS")
        n_entry = entry.values.tolist()[0]
        n_entry.extend([value, name])
        results_filename = results_path+name+".csv"
        print("READING RESULTS")
        if os.path.exists(results_filename):
            results = pd.read_csv(results_filename, sep=',', encoding="latin1")
        else:
            results = pd.DataFrame(columns=res_header)
        
        results.loc[len(results)] = n_entry
        results = results.drop_duplicates(keep="first")
        results.to_csv(results_filename, sep=',', index=False)
        # keeps track of how many times page was annotated
        increase_page_annotation_count(page, origin)
    else:
        print("ENTRY DOESNT EXIST")

def get_least_annotated_page(name,aPage=None):
    done_by_annotator, total_done = get_done_by_annotator(name)
    
    #Print number of annotated pages and total number of pages
    s_p = pd.read_csv(samples_path, sep='\t', encoding="latin1").sample(frac=1)
    print("done: ", len(done_by_annotator), " | total: ", len(s_p))
    
    if len(done_by_annotator) == len(s_p):
        return "Last annotation done! Thank you!", None, None, None, None, None, None, None

    #Creates or reads countfile:
    count_file = get_count_file(s_p)
    
    #Get pages not done by current annotator
    #not_done_count = ((count_file.loc[~(count_file['page']+count_file['source_url']).isin(done_by_annotator)])).sample(frac=1)
    not_done_count = (count_file[~(count_file.page.isin(done_by_annotator.page) & count_file.source_url.isin(done_by_annotator.source_url))]).sample(frac=1)
    
    print(">>",aPage)
    if aPage is not None:
        remOrigins = not_done_count.loc[not_done_count['page'] == aPage]
        if len(remOrigins)==0:
            return get_least_annotated_page(name)
    else:
        twice_annotated = (not_done_count.loc[not_done_count['count'] == 2]).sample(frac=1)
        if len(twice_annotated) > 0:
            print("TWICE")
            page = twice_annotated.iloc[0]['page']
        else:    
            once_annotated = (not_done_count.loc[not_done_count['count'] == 1]).sample(frac=1)
            if len(once_annotated) > 0:
                print("ONCE")
                page = once_annotated.iloc[0]['page']
            else:
                print("OTHER")
                index = (not_done_count['count']).sample(frac=1).idxmin(axis=0, skipna=True)
                page = not_done_count.loc[index]['page']
        remOrigins = not_done_count.loc[not_done_count['page'] == page]

    entry = remOrigins.iloc[0]
    entry = s_p[(s_p.page.isin([entry.page]) & s_p.source_url.isin([entry.source_url]))].iloc[0]
    
    a_page = entry.page.strip()
    print("CHOSEN PAGE")
    print(a_page)
    print("CHOSEN PAGE")
    o_page = entry.source_url.strip()
    print("CHOSEN SOURCE")
    print(o_page)
    print("CHOSEN SOURCE")
    src_lst = entry.source_list.strip()
    
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
    print("PATH FOUND")

    return a_page, o_page, a_html, str(o_html), src_lst, a_done, a_total, total_done

# VIEWS
def home(request):
	print("GOT INTO INDEX")
	user = request.user
	session = request.session
	print(user)
	print(user.username)
	if not user.is_authenticated:
		print("NOT LOGGED IN")
		return render(request, 'home.html')
	else:
		# return render(request, 'home.html', {'t1':"<html></html>", 't2':"<html></html>", 't3':"asda", 't4':"asdas", 'a_done':0, 'a_total':0, 't_done':0, 'alpha':0})
		print("USER LOGGED IN")
		name = user.username
		if request.method == 'POST':
			print("METHOD IS POST")
			op = request.POST.copy().get('op')
			if op:
				print("OP")
				print(op)
				print("OP")
				if op in list(op_dict.keys()):
					op = op_dict[op]
					print("OP NUM")
					print(op)
					print("OP NUM")
					if not ("test" in name):
						save_annotation(session.get('claim'),session.get('origin'), op, name)
					a_url, o_url, a_html, o_html, src_lst, a_done, a_total, t_done = get_least_annotated_page(name, session.get('claim'))
					# Turn string representation of a list to a list
					print("")
					print(a_url)
					print("")
					print("")
					print(o_url)
					print("")
					print("")
					print(src_lst)
					print("")
			else:
				a_url = session.get('claim')
				o_url = session.get('origin')
				a_html = session.get('a_html')
				o_html = session.get('o_html')
				src_lst = session.get('src_lst')
				a_done = session.get('a_done')
				a_total = session.get('a_total')
				t_done = session.get('t_done')
		else:
			a_url, o_url, a_html, o_html, src_lst, a_done, a_total, t_done = get_least_annotated_page(name)
			# Turn string representation of a list to a list
			print("")
			print(a_url)
			print("")
			print("")
			print(o_url)
			print("")
			print("")
			print(src_lst)
			print("")

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

		#Render home page (annotator)
		assert a_html is not None, "A_HTML IS NONE"
		assert o_html is not None, "O_HTML IS NONE"
		assert a_url is not None, "A_URL IS NONE"
		assert o_url is not None, "O_URL IS NONE"
		assert a_done is not None, "A_DONE IS NONE"
		assert a_total is not None, "A_TOTAL IS NONE"
		assert t_done is not None, "T_DONE IS NONE"

		print(a_url)
		print(o_url)

		return render(request, 'home.html', {'t1':a_html, 't2':o_html, 't3':a_url, 't4':o_url, 'a_done':a_done, 'a_total':a_total, 't_done':t_done})

def test(request):
	return render(request, 'test.html')

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

#Needs testing to work with Django, but logic is present
#Remember to check if path is correct in urls.py
def change_origin(request):
	if request.method == 'POST':
		session = request.session
		
		print("")
		print(request.body)
		print("")
		
		received = json.loads(request.body.decode())
		
		print("")
		print(received)
		print("")

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
			print("bad link")
			return JsonResponse({'msg': "bad", 'source': session.get('o_html'), 'n_link':curr_source_url, 'o_link':clicked_source_url})

		results_filename = results_path+request.user.username+".csv"
		#If new user, then nothing is annotated
		if not os.path.exists(results_filename):
			path_to_new_source = snopes_path+(page.strip("/").split("/")[-1]+"/")+str((src_idx_num))+".html"
			session["origin"] = clicked_source_url
			f = codecs.open(path_to_new_source, encoding='utf-8')
			o_html = bs(f.read(),"lxml")
			session['o_html'] = str(o_html)
			print("new user")
			return JsonResponse({'msg': "ok", 'source': session.get('o_html'), 'n_link':clicked_source_url, 'o_link':curr_source_url})
		else:
			results = pd.read_csv(results_filename, sep=',', encoding="latin1")
			target_row = results.loc[(results["page"] == page) & (results["source_url"] == clicked_source_url)]
			#Check if page+source are in results (ie already annotated link)
			if len(target_row) != 0:
				print("already done")
				return JsonResponse({'msg': "done", 'source': session.get('o_html'), 'n_link':curr_source_url, 'o_link':curr_source_url})
			#Means this is an old user who didnt annotate clicked link
			path_to_new_source = snopes_path+(page.strip("/").split("/")[-1]+"/")+str((src_idx_num))+".html"
			session["origin"] = clicked_source_url
			f = codecs.open(path_to_new_source, encoding='utf-8')
			o_html = bs(f.read(),"lxml")
			session['o_html'] = str(o_html)
			print("old user, not done")
			return JsonResponse({'msg': "ok", 'source': session.get('o_html'), 'n_link':clicked_source_url, 'o_link':curr_source_url})
	else:
		return JsonResponse({'msg': "error", "why" : "dont GET this page, only POST"})
