# -*- coding: utf-8 -*-
"""
Created on Wed Jun 19 16:56:07 2019

@author: Mohamad
"""
import os
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

from bs4 import BeautifulSoup as bs
import lxml
import urllib
import ast
import requests

cwd = os.getcwd()
session = requests.Session()
session.headers.update({'User-Agent': 'Custom user agent'})
#, headers={'User-Agent': 'a user agent'}
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument("--window-size=1920x1080")
chrome_driver = cwd+"/chromedriver"

samples_path = cwd+"/samples.csv"
output_path = cwd+"/samples_html.csv"
error_path = cwd+"/samples_error.csv"
smpls = pd.read_csv(samples_path, sep='\t', encoding="latin1")
s_d = smpls.to_dict('index')

write_header=True

for key in s_d:
    print("WILL TRY NEW PAGE")
    try:
        print("ABOUT TO REQUEST")
        st = session.get(s_d[key]["page"]).status_code
        print("DONE WITH REQUEST")
        if st == 502 or st == 302:
            print("ERROR CODE")
            s_d[key]["page_html"] = "err"
        elif st == 404:
            print("BAD CODE")
            s_d[key]["page_html"] = "bad"
        else:
            browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
            browser.get(s_d[key]["page"])
            print("ABOUT TO GET SOURCE")
            body = browser.page_source
            print("GOT BODY")
            body.replace('"','&').replace('&quot;','&amp;amp;')
            print("REPLACED QUOTES")
        
            #Disable non-origin links
            soup = bs(body, 'lxml')
            for a in soup.findAll('a'):
                if a.has_attr("href"):
                    if not (a['href'] in ast.literal_eval(s_d[key]["source_list"])):
                        del a['href']
                        a.name='span'
                    else:
                        a['id']=a['href']
            print("STOPPED LINKS")
            if len(soup.findAll('span')) > 0:
                soup.span.unwrap()
            
            # Remove all tags inside <a> tags, if any
            for a in soup.findAll('a'):
                words=a.get_text()
                a.clear()
                a.insert(1,words)
        
            decomposers = [s for s in soup.find_all(["span","div"]) if "Snopes Needs Your Help" in s.text]
            parents = [s.parent for s in decomposers if ("w-div" in s.parent.parent.get("class"))]
            parents2 = [s.parent.parent.parent for s in decomposers if ("w-div" in s.parent.parent.get("class"))]
            [p.decompose() for p in (parents+parents2)]
            print("GOT SOUP")
            body = str(soup)
        
            #Add code to higlight hyperlink of current origin and scroll to it
            injectionPoint=body.split("</body>")
            highlightFnc = '<script> function highlight(){ let link = parent.document.getElementById("oLink").href; document.getElementById(link).style.backgroundColor="yellow"; } if (window.attachEvent) {window.attachEvent("onload", highlight);} else if (window.addEventListener) {window.addEventListener("load", highlight, false);} else {document.addEventListener("load", highlight, false);} </script>'
            highlightLnkFnc = '<script> function highlightLnk(newLnk,oldLnk){document.getElementById(oldLnk).style.backgroundColor="white"; document.getElementById(newLnk).style.backgroundColor="yellow"; } </script></body>'
            scrollFnc = '<script> function scrollDown(){ let link = parent.document.getElementById("oLink").href; var elmnt = document.getElementById(link); elmnt.scrollIntoView({ behavior: "smooth", block: "nearest"  }); } if (window.attachEvent) {window.attachEvent("onload", scrollDown);} else if (window.addEventListener) {window.addEventListener("load", scrollDown, false);} else {document.addEventListener("load", scrollDown, false);} </script>'
            body=injectionPoint[0]+highlightFnc+scrollFnc+highlightLnkFnc+injectionPoint[1]
            
            #Add JQuery CDN and event-handler
            injectionPoint=body.split("</body>")
            jqueryCode='<script src="https://code.jquery.com/jquery-3.4.1.js" integrity="sha256-WpOohJOqMqqyKL9FccASB9O0KwACQJpFTUBLTYOVvVU=" crossorigin="anonymous"></script>'
            jqEvnt = '<script> $("a").on("click", function(e){ e.preventDefault(); if(e.target.href){ if(!(e.target.href == parent.document.getElementById("oLink").href)){ parent.document.getElementById("oframe").srcdoc="<p>LOADING..PLEASE WAIT</p>"; let link = e.target.href; let claim = parent.document.getElementById("cLink").href; $.ajax({ url: "/newOrigin", data: {"link":link, "claim":claim}, type: "POST", success: function(response) { if(response.st=="ok"){ parent.document.getElementById("oframe").srcdoc=response.site; parent.document.getElementById("oLink").href=response.link; highlightLnk(response.link, response.oldLnk); } else if (response.st=="bad"){ alert("Broken link :/");       parent.document.getElementById("oframe").srcdoc=response.site; } else{ alert("Link already annotated!");      parent.document.getElementById("oframe").srcdoc=response.site; } }, error:function(error) { console.log(error); } }); }}}); </script></body>'
            body=injectionPoint[0]+jqueryCode+jqEvnt+injectionPoint[1]
            for h in soup.find_all('html'):
                if len(str(h.contents))<1000:
                    s_d[key]["page_html"] = "bad"
            if ("page_html" not in s_d[key]):
                s_d[key]["page_html"] = bs(body,"lxml").prettify()
            print("done with article")
            browser.close()
    except Exception as e:
        print(e)
        print("EXCEPTION THROWN")
        s_d[key]["page_html"] = "err"
    
    try:
        st = session.get(s_d[key]["source_url"]).status_code
        if st == 502 or st == 302:
            print("ERROR CODE")
            s_d[key]["source_html"] = "err"
        elif st == 404:
            print("BAD CODE")
            s_d[key]["source_html"] = "bad"
        else:
            browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
            browser.get(s_d[key]["source_url"])
            print("ABOUT TO GET SOURCE")
            body = browser.page_source
            print("GOT BODY")
            body.replace('"','&').replace('&quot;','&amp;amp;')
            soup = bs(body, 'lxml')
            
            domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urllib.parse.urlparse(s_d[key]["source_url"]))
            
            for img in soup.findAll('img'):
                if img.has_attr('src'):
                    src = img['src']
                    if not src.startswith("http"):
                        img['src'] = domain+src
                        
            for h in soup.find_all('html'):
                if len(str(h.contents))<1000:
                    s_d[key]["source_html"] = "bad"
            if ("source_html" not in s_d[key]):
                s_d[key]["source_html"] = bs(body,"lxml").prettify()
            print("done with src")
            browser.close()
    except Exception as e:
        print(e)
        print("EXCEPTION THROWN")
        s_d[key]["source_html"] = "err"
      
        
    if((s_d[key]["source_html"] == "bad") or (s_d[key]["page_html"] == "bad")):
        continue
    elif((s_d[key]["source_html"] == "err") or (s_d[key]["page_html"] == "err")):
        to_append = pd.DataFrame([s_d[key]])
        print(to_append)
        to_append = to_append[["page", "claim", "verdict", "tags", "date", "author", "source_list", "source_url", "page_html", "source_html"]]
        to_append.to_csv(error_path, sep="\t", mode='a', index=False, header=write_header)
    else:
        to_append = pd.DataFrame([s_d[key]])
        print(to_append)
        to_append = to_append[["page", "claim", "verdict", "tags", "date", "author", "source_list", "source_url", "page_html", "source_html"]]
        to_append.to_csv(output_path, sep="\t", mode='a', index=False, header=write_header)
    write_header=False
browser.quit()