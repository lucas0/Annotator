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

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument("--window-size=1920x1080")
chrome_driver = cwd+"/chromedriver"

browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)

res_header = ["page", "claim", "verdict", "tags", "date", "author", "source_list", "source_url", "value", "name"]
samples_path = datadir+"/samples.csv"
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
        n_entry = entry.values.tolist()[0]
        n_entry.extend([value, name])
        results_filename = results_path+name+".csv"
        if os.path.exists(results_filename):
            results = pd.read_csv(results_filename, sep=',', encoding="latin1")
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
        results = pd.read_csv(results_filename, sep=',', encoding="latin1")
        done_by_annotator = (results["page"]+results["source_url"]).unique()
    else:
        done_by_annotator = []
    
    #Print number of annotated pages and total number of pages
    s_p = pd.read_csv(samples_path, sep='\t', encoding="latin1")
    print("done: ", len(done_by_annotator), " | total: ", len(s_p))
    
    if len(done_by_annotator) == len(s_p.page.unique()):
        return "Last annotation done! Thank you!", "Last annotation done! Thank you!", "Last annotation done! Thank you!", "Last annotation done! Thank you!"

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
    # entry = s_p.loc[s_p['page']==entry['page'] && s_p['source_url']==entry['source_url']][0]
    
    src_lst = entry.source_list.strip()
    totalPage = len(s_p.loc[s_p['page'] == entry.page])
    donePage = totalPage - len(remOrigins)
    # Check if origin is broken link or not
    try:
        o_status = requests.get(entry.source_url.strip(), headers={'User-Agent': 'a user agent'}).status_code
    except requests.exceptions.RequestException as e:
        return entry.page.strip(), entry.source_url.strip(), src_lst, donePage, totalPage,len(done_by_annotator)
    
    if o_status == requests.codes.ok:
        return entry.page.strip(), entry.source_url.strip(), src_lst, donePage, totalPage, len(done_by_annotator)
    else:
        save_annotation(entry.page.strip(), entry.source_url.strip(), '3', name)
        return get_least_annotated_page(name,entry.page.strip())

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
			data = request.POST.copy()
			op = data.get('op')
			alphaFromClient = data.get('alpha')
			if op and not (alphaFromSession == alphaFromClient):
				if op in ['1', '2', '3', '4']:
					save_annotation(session.get('claim'),session.get('origin'), op, name)
					session['alpha']=alphaFromClient
					a_url, o_url, src_lst, a_done, a_total, t_done = get_least_annotated_page(name, session.get('claim'))
					# Turn string representation of a list to a list
					src_lst = ast.literal_eval(src_lst)
			else:
				a_url = session.get('claim')
				o_url = session.get('origin')
				src_lst = session.get('src_lst')
				a_done = session.get('doneP')
				a_total = session.get('totalP')
				t_done = session.get('doneT')
		else:
			a_url, o_url, src_lst, a_done, a_total, t_done = get_least_annotated_page(name)
			# Turn string representation of a list to a list
			src_lst = ast.literal_eval(src_lst)
		
		print("GETTING ARTICLE WITH SELENIUM")
		try:
			browser.get(a_url)
		except TimeoutException as e:
			return redirect('home')

		a_html = browser.page_source

		print("DISABLING LINKS")
		#Disable non-origin links
		soup = BeautifulSoup(a_html, 'lxml')
		for a in soup.findAll('a'):
			if a.has_attr("href"):
				if not (a['href'] in src_lst):
					del a['href']
					a.name='span'
				else:
					a['id']=a['href']

		if len(soup.findAll('span')) > 0:
			soup.span.unwrap()

		print("REMOVING TAGS FROM A")
		# Remove all tags inside <a> tags, if any
		for a in soup.findAll('a'):
			words=a.get_text()
			a.clear()
			a.insert(1,words)

		decomposers = [s for s in soup.find_all(["span","div"]) if "Snopes Needs Your Help" in s.text]
		parents = [s.parent for s in decomposers if ("w-div" in s.parent.parent.get("class"))]
		parents2 = [s.parent.parent.parent for s in decomposers if ("w-div" in s.parent.parent.get("class"))]
		[p.decompose() for p in (parents+parents2)]

		a_html=str(soup)

		print("INJECTING JS SCRIPTS")
		#Add code to higlight hyperlink of current origin and scroll to it
		injectionPoint=a_html.split("</body>")
		highlightFnc = '<script> function highlight(){ let link = parent.document.getElementById("oLink").href; document.getElementById(link).style.backgroundColor="yellow"; } if (window.attachEvent) {window.attachEvent("onload", highlight);} else if (window.addEventListener) {window.addEventListener("load", highlight, false);} else {document.addEventListener("load", highlight, false);} </script>'
		highlightLnkFnc = '<script> function highlightLnk(newLnk,oldLnk){document.getElementById(oldLnk).style.backgroundColor="white"; document.getElementById(newLnk).style.backgroundColor="yellow"; } </script></body>'
		scrollFnc = '<script> function scrollDown(){ let link = parent.document.getElementById("oLink").href; var elmnt = document.getElementById(link); elmnt.scrollIntoView({ behavior: "smooth", block: "start"  }); } if (window.attachEvent) {window.attachEvent("onload", scrollDown);} else if (window.addEventListener) {window.addEventListener("load", scrollDown, false);} else {document.addEventListener("load", scrollDown, false);} </script>'
		a_html=injectionPoint[0]+highlightFnc+scrollFnc+highlightLnkFnc+injectionPoint[1]

		print("INJECTING JS SCRIPTS")
		#Add JQuery CDN and event-handler
		injectionPoint=a_html.split("</body>")
		jqueryCode='<script src="https://code.jquery.com/jquery-3.4.1.js" integrity="sha256-WpOohJOqMqqyKL9FccASB9O0KwACQJpFTUBLTYOVvVU=" crossorigin="anonymous"></script>'
		jqEvnt = '<script> $("a").on("click", function(e){ e.preventDefault(); if(e.target.href){ if(!(e.target.href == parent.document.getElementById("oLink").href)){ parent.document.getElementById("oframe").srcdoc="<p>LOADING..PLEASE WAIT</p>"; let link = e.target.href; let claim = parent.document.getElementById("cLink").href; $.ajax({ url: "/newOrigin", data: {"link":link, "claim":claim}, type: "POST", success: function(response) { if(response.st=="ok"){ parent.document.getElementById("oframe").srcdoc=response.site; parent.document.getElementById("oLink").href=response.link; highlightLnk(response.link, response.oldLnk); } else if (response.st=="bad"){ alert("Broken link :/");       parent.document.getElementById("oframe").srcdoc=response.site; } else{ alert("Link already annotated!");      parent.document.getElementById("oframe").srcdoc=response.site; } }, error:function(error) { console.log(error); } }); }}}); </script></body>'
		a_html=injectionPoint[0]+jqueryCode+jqEvnt+injectionPoint[1]

		print("GETTING SOURCE WITH SELENIUM")
		browser.get(o_url)
		o_html = browser.page_source

		print("FIXING LOCALLY REFERENCED SRCs")
		soup = BeautifulSoup(o_html, 'lxml')
		domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urlparse(o_url))
		for img in soup.findAll('img'):

			if img.has_attr('src'):
				src = img['src']
				if not src.startswith("http"):
					src.lstrip("/")
					img['src'] = domain+src

		o_html = soup.prettify()

		#Save claim and origin links and list of origins in session
		session['claim'] = a_url
		session['origin'] = o_url
		session['src_lst'] = src_lst
		session['a_done'] = a_done
		session['a_total'] = a_total
		session['t_done'] = t_done	

		alpha=session.get('alpha')

		#Render home page (annotator)
		# print(a_html[:10])
		# print(o_html[:10])
		# print(a_url)
		# print(o_url)
		# print(a_done)
		# print(a_total)
		# print(t_done)
		# print(alpha)
		
		return render(request, 'home.html', {'t1':a_html, 't2':o_html, 't3':a_url, 't4':o_url, 'a_done':a_done, 'a_total':a_total, 't_done':t_done, 'alpha':alpha})

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