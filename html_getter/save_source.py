import os
import pandas as pd

from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

from bs4 import BeautifulSoup as bs
import lxml
import urllib
import ast

cwd = os.getcwd()

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument("--window-size=1920x1080")
chrome_driver = cwd+"/chromedriver"

#Change paths
samples_path = cwd+"/samples.csv"
output_path = cwd+"/samples_html.csv"
log_path = cwd+"/samples_error.csv"

samples = pd.read_csv(samples_path, sep='\t', encoding="latin1")

#Header to be used when saving to samples_html.csv
header = list(samples.columns.values).extend(['page_html','source_html'])

#Change delimitter
def logError(url, message):
    with open(log_path, "a+") as log:
        to_write_to_file = url+"<|>"+str(message) #using comma in .write() function gives error
        log.write(to_write_to_file)

def get_html(url):
    try:
        browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
        browser.header_overrides = {'User-Agent': 'Custom user agent'}
        browser.get(url)
        for req in browser.requests:
            if req.response:
                st = req.response.status_code
                if st == 301:
                    #redirection, we need to get the status-code of the next request
                    #note: html retrieved from such sites CAN be valid, some snopes links give this code
                    continue
                else:
                    break #Only need first code after the final 301 (redirect) if any
        print("MOHAMED, STATUS CODE: ",st)
        if st == 404 or st == 301:
            return "error"
        elif st == 502:
            logError(url, st)
            return "error"
        html = browser.page_source
        if len(html) < 1000:
            logError(url, "size")
            return "error"
        else:
            return html
    except Exception as e:
        print("Exception")
        logError(url, e)
        return "error"
    finally:
        browser.quit()
#Used to check whether or not this will be the first write to samples_html.csv
first_entry=True

for idx, e in samples.iterrows():
    print("TRYING NEW ROW")
    a_html = get_html(e.page)
    o_html = get_html(e.source_url)
    if "error" in [a_html,o_html]:
        print("GOT ERROR")
        print("MOHAMED, a_html:",a_html)
        print("MOHAMED, o_html:",o_html)
        continue
    else:
        print("PROCEEDING")
        print("PROCESS PAGE HTML")
        #Disable non-origin links
        soup = bs(a_html, 'lxml')
        for a in soup.find_all('a'):
            if a.has_attr("href"):
                if not (a['href'] in ast.literal_eval(e.source_list)):
                    del a['href']
                    a.name='span'
                else:
                    a['id']=a['href']
                    #Remove tags inside link, to leave only text
                    words=a.get_text()
                    a.clear()
                    a.insert(1,words)
                    #Make the link a child tag of the paragraph (ie remove all tags between link and paragraph) <p><nobr><a></a></nobr></p> becomes <p><a></a></p>. Important for injected Javascript functions.
                    if a.parent.name != "p":
                        curr_parent = a.parent
                        old_parent = curr_parent
                        while curr_parent.name != "p":
                            old_parent = curr_parent
                            curr_parent = curr_parent.parent
                        old_parent.replace_with(a)

        if len(soup.find_all('span')) > 0:
            soup.span.unwrap()

        #removes the overlay
        decomposers = [s for s in soup.find_all(["span","div"]) if "Snopes Needs Your Help" in s.text]
        parents = []
        [parents.extend(s.find_parents('w-div')) for s in decomposers]
        [p.decompose() for p in parents if p is not None]
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
        print("DONE WITH PAGE HTML")
        a_html = bs(body,"lxml").prettify()

        print("PROCESSING SOURCE HTML")
        domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urllib.parse.urlparse(o_html))
        soup = bs(o_html, 'lxml')

        for elem in soup.find_all(['img', 'script']):
            if elem.has_attr('src'):
                src = elem['src']
                if not src.startswith("http"):
                    src.lstrip("/")
                    elem['src'] = domain+src
        
        #Will turn list into dictionary then append to dataframe
        #NEEDS TO BE RE-WRITTEN. DOES NOT WORK PROPERLY
        samples_html = pd.DataFrame(columns=header)
        
        entry = e.values.tolist()
        entry.extend([a_html, o_html])
        
        dict_entry = dict(zip(header, entry))
        samples_html = samples_html.append(dict_entry, ignore_index=True)
        
        samples_html.to_csv(output_path, sep='\t', index=False, columns=header,header=first_entry,mode='a')
        first_entry=False