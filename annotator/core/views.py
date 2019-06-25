from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.http import JsonResponse

import os, sys
import pandas as pd

from bs4 import BeautifulSoup as bs
import lxml
import ast

cwd = os.path.abspath(__file__+"/..")
data_dir = os.path.abspath(cwd+"/../data")
html_dir = os.path.abspath(cwd+"/../../html_getter")
samples_path = html_dir+"/samples_html_no_err.csv"

res_header = ["page", "claim", "verdict", "tags", "date", "author", "source_list", "source_url", "value", "name"]

samples_path = data_dir+"/samples.csv"
samples_path = html_dir+"/samples_html_no_err.csv"
results_path = data_dir+"/results/"
a_html_path = data_dir+"/pages_html/"
o_html_path = data_dir+"/sources_html/"
count_path = data_dir+"/count.csv"
# AUX FUNCTIONS

def increase_page_annotation_count(page, origin):
    count_file = pd.read_csv(count_path, sep=',', encoding="utf_8")
    count_file.loc[(count_file['page'] == page) & (count_file['source_url'] == origin), 'count'] += 1
    count_file.to_csv(count_path, sep=',', index=False)

def save_annotation(page, origin, value, name):
    # Read samples file
    print("SAVING ANNOTATION")
    s_p = pd.read_csv(samples_path, sep='\t', encoding="utf_8")
    entry = s_p.loc[(s_p["page"] == page) & (s_p["source_url"] == origin)]
    if not (entry.empty):
        entry = entry.drop(columns=['page_html','source_html'])
        n_entry = entry.values.tolist()[0]
        n_entry.extend([value, name])
        results_filename = results_path+name+".csv"
        if os.path.exists(results_filename):
            results = pd.read_csv(results_filename, sep=',', encoding="utf_8")
        else:
            results = pd.DataFrame(columns=res_header)
        oldEntry = results.loc[(results["page"] == page) & (results["source_url"] == origin)]
        if oldEntry.empty:
            results.loc[len(results)] = n_entry
        results.to_csv(results_filename, sep=',', index=False)
        # keeps track of how many times page was annotated
        increase_page_annotation_count(page, origin)

def get_least_annotated_page(name,aPage=None):
    # creates a list of pages that have been already annotated by the current annotator
    results_filename = results_path+name+".csv"
    if os.path.exists(results_filename):
        results = pd.read_csv(results_filename, sep=',', encoding="utf_8")
        done_by_annotator = (results["page"]+results["source_url"]).unique()
    else:
        done_by_annotator = []
    
    #Print number of annotated pages and total number of pages
    s_p = pd.read_csv(samples_path, sep='\t', encoding="utf_8")
    print("done: ", len(done_by_annotator), " | total: ", len(s_p))
    
    if len(done_by_annotator) == len(s_p):
        return "Last annotation done! Thank you!", None, None, None, None, None, None, None

    #Creates or reads countfile:
    if os.path.exists(count_path):
        count_file = pd.read_csv(count_path, sep=',', encoding="utf_8").sample(frac=1)
    else:
        count_file = s_p[['page','source_url']].copy()
        count_file['count'] = 0
        count_file.to_csv(count_path, sep=',', index=False)
        
    #Get pages not done by current annotator
    count_file = count_file.loc[~(count_file['page']+count_file['source_url']).isin(done_by_annotator)]
    

    print(">>",aPage)
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
    src_lst = entry.source_list.strip()

    with open(a_html_path+a_page+".html", "r+") as f:
        a_html = bs(f.read(),"lxml")
    with open(o_html_path+o_page+".html", "r+") as f:
        o_html = bs(f.read(),"lxml")

    a_total = len(s_p.loc[s_p['page'] == entry.page])
    a_done  = a_total - len(remOrigins)

    # soup = bs(a_html, "lxml")
    # decomposers = [s for s in soup.find_all(["span","div"]) if "Snopes Needs Your Help" in s.text]
    # parents = []
    # [parents.extend(s.find_parents('w-div')) for s in decomposers]
    # [p.decompose() for p in parents if p is not None]
    # body = str(soup)

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
		if request.method == 'POST':
			op = request.POST.copy().get('op')
			if op:
				if op in ['1', '2', '3', '4']:
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
					#src_lst = ast.literal_eval(src_lst)
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
			#src_lst = ast.literal_eval(src_lst)
		
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

#Needs testing to work with Django, but logic is present
#Remember to check if path is correct in urls.py
def newOrigin(request):
    page = request.body.get('claim')
    curr_source = request.body.get('curr_source')
    clicked_source = request.body.get('clicked_source')
    
    s_p = pd.read_csv(samples_path, sep='\t', encoding="utf_8")
    nxt = s_p.loc[(s_p["page"] == page) & (s_p["source_url"] == clicked_source)]
    #Check if page+source are in samples (ie valid link)
    if not nxt:
        curr = s_p.loc[(s_p["page"] == page) & (s_p["source_url"] == curr_source)]
        return JsonResponse({'msg': "bad", 'html': curr.source_html, 'url':curr_source})
    
    results_filename = results_path+request.user.username+".csv"
    #If new user, then nothing is annotated
    if not os.path.exists(results_filename):
        session["origin"] = nxt.source_url
        session['o_html'] = nxt.source_html
        return JsonResponse({'msg': "ok", 'html': nxt.source_html, 'url':nxt.source_url})
    else:
        results = pd.read_csv(results_filename, sep=',', encoding="utf_8")
        target_row = results.loc[(results["page"] == page) & (results["source_url"] == clicked_source)]
        #Check if page+source are in results (ie already annotated link)
        if target_row:
            return JsonResponse({'msg': "done", 'html': curr.source_html, 'url':curr_source})
        #Means this is an old user who didnt annotate clicked link
        session["origin"] = nxt.source_url
        session['o_html'] = nxt.source_html
        return JsonResponse({'msg': "ok", 'html': nxt.source_html, 'url':nxt.source_url})