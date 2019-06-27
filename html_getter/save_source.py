import os, sys
import re
import pandas as pd

from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

from bs4 import BeautifulSoup as bs
import lxml
import urllib
import ast

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

samples = pd.read_csv(samples_path, sep='\t', encoding="latin1")
num_samples = len(samples)

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
        browser.header_overrides = {'User-Agent': 'Custom user agent'}
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
        continue

    else:

        if a_html is not "done":
            print("PAGE HTML")
            #Disable non-origin links
            soup = bs(a_html, 'lxml')
            for a in soup.find_all('a'):
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
                            while curr_parent.name not in ["p","div"]:
                                old_parent = curr_parent
                                curr_parent = curr_parent.parent
                            old_parent.replace_with(a)

            #removes the overlay
            decomposers = [s for s in soup.find_all(["span","div"]) if "Snopes Needs Your Help" in s.text]
            parents = []
            [parents.extend(s.find_parents('w-div')) for s in decomposers]
            [p.decompose() for p in parents if p is not None]

            #body = body.replace("overflow: hidden", "overflow: scroll").replace("overflow-x: hidden", "overflow-x: scroll").replace("overflow-y: hidden", "overflow-y: scroll")
            b = soup.find("body")
            #in-line style
            if b.has_attr("style"):
                s = b["style"]
                #print(s)
                s = re.sub(r'overflow:.+?(?=[;}])','overflow: scroll',s)
                s = re.sub(r'overflow-y:.+?(?=[;}])','overflow-y: scroll',s)
                s = re.sub(r'overflow-x:.+?(?=[;}])','overflow-x: scroll',s)
                b["style"] = s
                #print(soup.find("body")["style"])

            #style is a tag
            if b.find("style") is not None:
                s = b.style.string
                s = re.sub(r'overflow:.+?(?=[;}])','overflow: scroll',s)
                s = re.sub(r'overflow-y:.+?(?=[;}])','overflow-y: scroll',s)
                s = re.sub(r'overflow-x:.+?(?=[;}])','overflow-x: scroll',s)
                #print(s)
                soup.find("body").style.string.replace_with(s)
                #print(b.style.prettify())

            body = str(soup)
            #Add code to higlight hyperlink of current origin and scroll to it
            injectionPoint=body.split("</body>")

            highlightFnc = '<script> function highlight(){ let link = parent.document.getElementById("oLink").href; document.getElementById(link).style.backgroundColor="yellow"; } if (window.attachEvent) {window.attachEvent("onload", highlight);} else if (window.addEventListener) {window.addEventListener("load", highlight, false);} else {document.addEventListener("load", highlight, false);} </script>'
            scrollFnc = '<script> function scrollDown(){ let link = parent.document.getElementById("oLink").href; var elmnt = document.getElementById(link); elmnt.scrollIntoView({ behavior: "smooth", block: "nearest"  }); } if (window.attachEvent) {window.attachEvent("onload", scrollDown);} else if (window.addEventListener) {window.addEventListener("load", scrollDown, false);} else {document.addEventListener("load", scrollDown, false);} </script>'
            highlightLnkFnc = '<script> function highlightLnk(newLnk,oldLnk){document.getElementById(oldLnk).style.backgroundColor="white"; document.getElementById(newLnk).style.backgroundColor="yellow"; } </script></body>'

            #Add JQuery CDN and event-handler
            jqueryCode='<script src="https://code.jquery.com/jquery-3.4.1.js" integrity="sha256-WpOohJOqMqqyKL9FccASB9O0KwACQJpFTUBLTYOVvVU=" crossorigin="anonymous"></script>'
            jqEvnt='<script> $("a").on("click", function(e){ e.preventDefault(); if(e.target.href){ if(!(e.target.href == parent.document.getElementById("oLink").href)){ parent.document.getElementById("oFrame").srcdoc = "<p>LOADING..PLEASE WAIT</p>"; let clicked_source = e.target.href; let csrf_tok = parent.document.getElementById("csrf_tok").value; $.ajax({ url: "/change_origin/", data: JSON.stringify({"clicked_source":clicked_source}), type: "POST", beforeSend: function (xhr, settings) { xhr.setRequestHeader("X-CSRFToken", csrf_tok );}, success: function(response) { if(response.msg=="ok"){ parent.document.getElementById("oFrame").srcdoc=response.source; parent.document.getElementById("oLink").href=response.n_link; highlightLnk(response.n_link,response.o_link)} else if (response.msg=="bad"){ alert("Broken link :/"); parent.document.getElementById("oFrame").srcdoc=response.source; } else{ alert("Link already annotated!"); parent.document.getElementById("oFrame").srcdoc=response.source; } }, error:function(error) { console.log(error); } }); } } }); </script></body>'
            #jqEvnt='<script> $("a").on("click", function(e){ e.preventDefault(); if(e.target.href){ if(!(e.target.href == parent.document.getElementById("oLink").href)){ parent.document.getElementById("oFrame").srcdoc = "<p>LOADING..PLEASE WAIT</p>"; let clicked_source = e.target.href; $.ajax({ url: "/change_origin/", data: JSON.stringify({"clicked_source":clicked_source}), type: "POST", beforeSend: function (xhr, settings) { xhr.setRequestHeader("X-CSRFToken", "{{ csrf_token }}");}, success: function(response) { if(response.msg=="ok"){ parent.document.getElementById("oFrame").srcdoc=response.source; parent.document.getElementById("oLink").href=response.n_link; highlightLnk(response.n_link,response.o_link)} else if (response.msg=="bad"){ alert("Broken link :/"); parent.document.getElementById("oFrame").srcdoc=response.source; } else{ alert("Link already annotated!"); parent.document.getElementById("oFrame").srcdoc=response.source; } }, error:function(error) { console.log(error); } }); } } }); </script></body>'

            body=injectionPoint[0]+highlightFnc+scrollFnc+highlightLnkFnc+jqueryCode+jqEvnt+injectionPoint[1]


            a_html = bs(body,'lxml')

            # save
            with open(a_html_filename, "w+", encoding='utf-8') as f:
                f.write(str(a_html))
                #f.write(a_html)
        else:
            print("PAGE ALREADY SAVED")

        if o_html is not "done":
            print("SOURCE HTML")
            domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urllib.parse.urlparse(o_html))
            soup = bs(o_html, 'lxml')

            for elem in soup.find_all(['img', 'script']):
                if elem.has_attr('src'):
                    src = elem['src']
                    if not src.startswith("http"):
                        src.lstrip("/")
                        elem['src'] = domain+src

            o_html = soup

            with open(o_html_filename, "w+", encoding='utf-8') as f:
                f.write(str(o_html))
                #f.write(o_html)
        else:
            print("SOURCE ALREADY SAVED")
