import os, sys
import re
import pandas as pd

from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import requests

from bs4 import BeautifulSoup as bs
import lxml
import urllib
import ast
import time

cwd = os.path.abspath(__file__+"/..")
parent_path = os.path.abspath(__file__+"/../../")
data_dir = os.path.abspath(cwd+"/../annotator/data/")

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument("--window-size=1920x1080")
chrome_driver = parent_path+"/chromedriver"

samples_path = data_dir+"/samples.csv"
log_path = cwd+"/log_error.csv"
html_path = data_dir+"/html_snopes/"
error_path = data_dir+"/bad_links.csv"

samples = pd.read_csv(samples_path, sep='\t', encoding="utf_8")
num_samples = len(samples)
out_header = ["page", "claim", "verdict", "tags", "date", "author","source_list","source_url"]
req_header = {'User-Agent': 'a user agent'}

def get_correct_path(lst, d, src):
    list_for_this_elem = lst
    dom = d
    while True:
        try:
            start=time.time()	
            r = requests.get(dom + src, headers=req_header, timeout=5)
            end = time.time()
            print("TIME TAKEN")
            print(end - start)
            print("TIME TAKEN")
            if r.status_code == requests.codes.ok:
                break
        except requests.exceptions.RequestException as e:
            print("REQUESTS EXCEPTION")
            print(e)
            print("REQUESTS EXCEPTION")
        if not (list_for_this_elem):
            break
        dom = dom + list_for_this_elem[0] + "/"
        list_for_this_elem.pop(0)
    return dom

#Change delimitter
def logError(url, message):
    message = url+"<|>"+str(message)+"\n" #using comma in .write() function gives error
    with open(log_path, "r+") as log:
        lines = log.readlines()
    if message not in lines:
        with open(log_path, "a+") as log:
            log.write(message)

def get_html(url):
    try:
        browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
        browser.header_overrides = {'User-Agent': 'Custom user agent', 'ORG_UNIT':'IT'}
        browser.get(url)
        for req in browser.requests:
            if req.response:
                st = req.response.status_code
        print("STATUS CODE: ",st)
        if st == 404 or st == 301:
            return "error"
        elif st == 502:
            logError(url, st)
            return "error"
        html = browser.page_source
        if len(html) < 1000:
            print("HTML SIZE PROBLEM")
            logError(url, "size")
            return "error"
        else:
            return html
    except Exception as e:
        print("GET HTML EXCEPTION")
        logError(url, e)
        return "error"
    finally:
        browser.quit()

is_first = not (os.path.exists(error_path))

#Used to check whether or not this will be the first write to samples_html.csv
for idx, e in samples.iterrows():
    print("\n|> ROW: ",idx,"/",num_samples)
    a_dir_name = html_path+e.page.strip("/").split("/")[-1]+"/"

    if not os.path.exists(a_dir_name):
        os.makedirs(a_dir_name)

    src_list =  ast.literal_eval(e.source_list)
    o_idx = src_list.index(e.source_url)

    a_html_filename = a_dir_name+"page.html"
    o_html_filename = a_dir_name+str(o_idx)+".html"

    a_html = "done" if os.path.exists(a_html_filename) else get_html(e.page)
    o_html = "done" if os.path.exists(o_html_filename) else get_html(e.source_url)

    if "error" in [a_html,o_html]:
        output = pd.DataFrame(columns=out_header)
        entry = e.values.tolist()
        output.loc[len(output)] = entry
        output.to_csv(error_path, sep='\t', header=is_first, index=False, mode='a')
        is_first = False

    else:

        if a_html is not "done":
            print("PAGE HTML")
            # Remove all comments from html
            a_html = re.sub("(<!--.*?-->)", "", a_html)
            soup = bs(a_html, 'lxml')

            #Disable non-origin links
            for a in soup.find_all('a'):
                if str(a) != "<None></None>":
                    if a.has_attr("href"):
                        if not (a['href'] in ast.literal_eval(e.source_list)):
                            a.unwrap()
                        else:
                            a['id']=a['href']
                            #Remove tags inside link, to leave only text
                            words=a.get_text()
                            a.clear()
                            a.insert(1,words)
                            #Make the link a child tag of the paragraph (ie remove all tags between link and paragraph) <p><nobr><a></a></nobr></p> becomes <p><a></a></p>. Important for injected Javascript functions.
                            if a.parent.name not in ["p","div"]:
                                curr_parent = a.parent
                                old_parent = curr_parent
                                if curr_parent is not None:
                                    while curr_parent.name not in ["p","div"]:
                                        old_parent = curr_parent
                                        curr_parent = curr_parent.parent
                                        if curr_parent is None:
                                            break
                                    if curr_parent is not None:
                                        old_parent.replace_with(a)

            #Remove snopes top banner
            for d in soup.find_all('div'):
                if str(d) != "<None></None>":
                    if d.has_attr("class"):
                        if ("theme-header-wrapper" in d["class"] or "theme-header" in d["class"]):
                            d.decompose()

            #removes the overlay
            decomposers = [s for s in soup.find_all(["span","div"]) if "Snopes Needs Your Help" in s.text]
            parents = []
            [parents.extend(s.find_parents('w-div')) for s in decomposers]
            [p.decompose() for p in parents if p is not None]


            b = soup.find("body")
            #in-line style
            if b.has_attr("style"):
                s = b["style"]
                s = re.sub(r'overflow:.+?(?=[;}])','overflow: scroll',s)
                s = re.sub(r'overflow-y:.+?(?=[;}])','overflow-y: scroll',s)
                s = re.sub(r'overflow-x:.+?(?=[;}])','overflow-x: scroll',s)
                # If original style didnt have overflow in it, add it
                if (s == b["style"]):
                	s = s + " overflow: scroll;"
                b["style"] = s
            else:
            	# If there was no style attribute
            	b["style"] = "overflow: scroll;"

            # List intitally only has body as we always want to change body style
            class_list = ["body"]
            # Get body tag
            b = soup.find("body")
            # if statement is for error checking, nothing more
            if b:
                if b.has_attr("class"):
                    classes = b["class"]
                    if type(classes) == list:
                        print("true is list")
                        class_list = class_list + classes
                    else:
                        print("false isnt list")
                        class_list.append(classes)

            body = str(soup)
            # Go over all styles affecting body (bode + classes) and change overflow
            for body_class in class_list:
                # Get css rule affecting body
                pattern = body_class +'{.+?(})'
                class_style = re.search(str(pattern), body) 
                if class_style:
                    # Turn to string and substitute value of overflow with scroll
                    class_style = class_style.group(0)
                    changed_style = re.sub(r'overflow:.+?(?=[;}])','overflow: scroll',class_style)
                    # Replace in body string
                    body = body.replace(class_style, changed_style)

            
            injectionPoint=body.split("</body>")
            # Code to higlight the pressed link
            highlightLnkFnc = '<script> function highlightLnk(newLnk,oldLnk){document.getElementById(oldLnk).style.backgroundColor="white"; document.getElementById(newLnk).style.backgroundColor="yellow"; } </script>'

            # JQuery CDN and event-handler
            jqueryCode='<script src="https://code.jquery.com/jquery-3.4.1.js" integrity="sha256-WpOohJOqMqqyKL9FccASB9O0KwACQJpFTUBLTYOVvVU=" crossorigin="anonymous"></script>'
            jqEvnt='<script> $("a").on("click", function(e){ e.preventDefault(); if(e.target.href){ if(!(e.target.href == parent.document.getElementById("oLink").href)){ parent.document.getElementById("oFrame").srcdoc = "<p>LOADING..PLEASE WAIT</p>"; let clicked_source = e.target.href; console.log(clicked_source); let csrf_tok = parent.document.getElementById("csrf_tok").value; $.ajax({ url: "/change_origin/", data: JSON.stringify({"clicked_source":clicked_source}), type: "POST", beforeSend: function (xhr, settings) { xhr.setRequestHeader("X-CSRFToken", csrf_tok );}, success: function(response) { if(response.msg=="ok"){ parent.document.getElementById("oFrame").srcdoc=response.source; parent.document.getElementById("oLink").href=response.n_link; highlightLnk(response.n_link,response.o_link)} else if (response.msg=="bad"){ alert("Broken link :/"); parent.document.getElementById("oFrame").srcdoc=response.source; } else{ alert("Link already annotated!"); parent.document.getElementById("oFrame").srcdoc=response.source; } }, error:function(error) { console.log(error); } }); } } }); </script></body>'
            
            body=injectionPoint[0]+highlightLnkFnc+jqueryCode+jqEvnt+injectionPoint[1]


            a_html = bs(body,'lxml')

            # save
            with open(a_html_filename, "w+", encoding='utf-8') as f:
                f.write(str(a_html))
        else:
            print("PAGE ALREADY SAVED")

        if o_html is not "done":
            print("SOURCE HTML")
            o_html = re.sub("(<!--.*?-->)", "", o_html)
            domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urllib.parse.urlparse(e.source_url))
            without_domain = (e.source_url).replace(domain, "")
            soup = bs(o_html, 'lxml')
            for elem in soup.find_all(['img', 'script', 'link', 'input']):
                if str(elem) != "<None></None>":
                    if elem.has_attr('src'):
                        src = elem['src']
                        if not src.startswith("http"):
                            list_for_this_elem = without_domain.split("/")
                            src.lstrip("/")
                            elem['src'] = get_correct_path(list_for_this_elem, domain, src) + src
                    if elem.has_attr('href'):
                        src = elem['href']
                        if not src.startswith("http"):
                            list_for_this_elem = without_domain.split("/")
                            src.lstrip("/")
                            elem['href'] = get_correct_path(list_for_this_elem, domain, src) + src
            o_html = soup

            with open(o_html_filename, "w+", encoding='utf-8') as f:
                f.write(str(o_html))
        else:
            print("SOURCE ALREADY SAVED")