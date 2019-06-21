from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate

import os, sys
import pandas as pd
from urllib.parse import urlparse

from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

from bs4 import BeautifulSoup
import lxml
import ast
import requests

cwd = os.path.abspath(__file__+"/..")
datadir = os.path.abspath(cwd+"/../data")
html_dir = os.path.abspath(cwd+"/../../html_getter")
samples_path = html_dir+"/samples_html_no_err.csv"

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument("--window-size=1920x1080")
chrome_driver = cwd+"/chromedriver"

browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)

res_header = ["page", "claim", "verdict", "tags", "date", "author", "source_list", "source_url", "value", "name"]
samples_path = datadir+"/samples.csv"
samples_path = html_dir+"/samples_html_no_err.csv"
results_path = datadir+"/results/"
count_path = datadir+"/count.csv"
# AUX FUNCTIONS

def increase_page_annotation_count(page, origin):
    count_file = pd.read_csv(count_path, sep=',', encoding="latin1")
    count_file.loc[(count_file['page'] == page) & (count_file['source_url'] == origin), 'count'] += 1
    count_file.to_csv(count_path, sep=',', index=False)

def save_annotation(page, origin, value, name):
    # Read samples file
    print("SAVING ANNOTATION")
    s_p = pd.read_csv(samples_path, sep='\t', encoding="latin1")
    entry = s_p.loc[(s_p["page"] == page) & (s_p["source_url"] == origin)]
    if not (entry.empty):
        entry = entry.drop(columns=['page_html','source_html'])
        n_entry = entry.values.tolist()[0]
        n_entry.extend([value, name])
        results_filename = results_path+name+".csv"
        if os.path.exists(results_filename):
            results = pd.read_csv(results_filename, sep=',', encoding="latin1")
        else:
            results = pd.DataFrame(columns=res_header)
        oldEntry = results.loc[(results["page"] == page) & (results["source_url"] == origin)]
        if oldEntry.empty:
            print(n_entry)
            print(len(n_entry))
            results.loc[len(results)] = n_entry
        results.to_csv(results_filename, sep=',', index=False)
        # keeps track of how many times page was annotated
        increase_page_annotation_count(page, origin)

def get_least_annotated_page(name,aPage=None):
    # creates a list of pages that have been already annotated by the current annotator
    results_filename = results_path+name+".csv"
    if os.path.exists(results_filename):
        results = pd.read_csv(results_filename, sep=',', encoding="latin1")
        done_by_annotator = (results["page"]+results["source_url"]).unique()
    else:
        done_by_annotator = []
    
    #Print number of annotated pages and total number of pages
    s_p = pd.read_csv(samples_path, sep='\t', encoding="latin1")
    print("done: ", len(done_by_annotator), " | total: ", len(s_p))
    
    if len(done_by_annotator) == len(s_p.page.unique()):
        return "Last annotation done! Thank you!", None, None, None, None, None, None, None

    #Creates or reads countfile:
    if os.path.exists(count_path):
        count_file = pd.read_csv(count_path, sep=',', encoding="latin1").sample(frac=1)
    else:
        count_file = s_p[['page','source_url']].copy()
        count_file['count'] = 0
        count_file.to_csv(count_path, sep=',', index=False)
        
    #Get pages not done by current annotator
    count_file = count_file.loc[~(count_file['page']+count_file['source_url']).isin(done_by_annotator)]
    
    if aPage is not None:
        remOrigins = count_file.loc[count_file['page'] == aPage]
        if len(remOrigins)==0:
            return get_least_annotated_page(name)
    else:
        twice_annotated = count_file.loc[count_file['count'] == 2]
        if len(twice_annotated) > 0:
            page = twice_annotated.iloc[0]['page']
        else:    
            once_annotated = count_file.loc[count_file['count'] == 1]
            if len(once_annotated) > 0:
                page = once_annotated.iloc[0]['page']
            else:
                index = count_file['count'].idxmin(axis=0, skipna=True)
                page = count_file.loc[index]['page']
        remOrigins = count_file.loc[count_file['page'] == page]
        
    entry = remOrigins.iloc[0]
    entry = s_p[(s_p.page.isin([entry.page]) & s_p.source_url.isin([entry.source_url]))].iloc[0]
    a_page = entry.page.strip()
    o_page = entry.source_url.strip()
    a_html = entry.page_html.strip()
    o_html = entry.source_html.strip()
    src_lst = entry.source_list.strip()

    a_total = len(s_p.loc[s_p['page'] == entry.page])
    a_done  = a_total - len(remOrigins)

    return a_page, o_page, a_html, o_html, src_lst, a_done, a_total, len(done_by_annotator)

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
		alphaFromSession = session.get('alpha')
		if request.method == 'POST':
			op = request.POST.copy().get('op')
			if op:
				if op in ['1', '2', '3', '4']:
					save_annotation(session.get('claim'),session.get('origin'), op, name)
					a_url, o_url, a_html, o_html, src_lst, a_done, a_total, t_done = get_least_annotated_page(name, session.get('claim'))
					# Turn string representation of a list to a list
					src_lst = ast.literal_eval(src_lst)
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
			src_lst = ast.literal_eval(src_lst)
		
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
