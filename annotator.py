from flask import Flask, flash, request, Response, url_for, redirect, session, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from app import app
from app import db
from app.models import User
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

cwd = os.getcwd()

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument("--window-size=1920x1080")
chrome_driver = cwd+"/chromedriver"

browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)

res_header = ["page", "claim", "verdict", "tags", "date", "author", "source_list", "source_url", "value", "name"]
samples_path = cwd+"/data/samples.csv"
results_path = cwd+"/data/results/"
count_path = cwd+"/data/count.csv"
db.create_all()


def increase_page_annotation_count(page, origin):
    count_file = pd.read_csv(count_path, sep=',', encoding="latin1")
    count_file.loc[(count_file['page'] == page)&(count_file['source_url'] == origin), 'count'] += 1
    count_file.to_csv(count_path, sep=',', index=False)


def save_annotation(page, origin, value, name):
    # Read samples file
    s_p = pd.read_csv(samples_path, sep='\t', encoding="latin1")
    entry = s_p.loc[(s_p["page"] == page) & (s_p["source_url"] == origin)]
    n_entry = entry.values.tolist()[0]
    n_entry.extend([value, name])
    results_filename = results_path+name+".csv"
    if os.path.exists(results_filename):
        results = pd.read_csv(results_filename, sep=',', encoding="latin1")
    else:
        results = pd.DataFrame(columns=res_header)
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
    print("done: ", len(done_by_annotator),
          " | total: ", len(s_p))
    if len(done_by_annotator) == len(s_p.page.unique()):
        return "Last annotation done! Thank you!", "Last annotation done! Thank you!", "Last annotation done! Thank you!", "Last annotation done! Thank you!"

    # creates or reads countfile:
    if os.path.exists(count_path):
        count_file = pd.read_csv(count_path, sep=',', encoding="latin1").sample(frac=1)
    else:
        count_file = s_p[['page','source_url']].copy()
        count_file['count'] = 0
        count_file.to_csv(count_path, sep=',', index=False)
        
    #Get pages not done by current annotator
    count_file = count_file.loc[~(count_file['page']+count_file['source_url']).isin(done_by_annotator)]
    
    #Check if there are, and retrieve, other origins of aPage 
    if aPage is not None:
        remOrigins = count_file.loc[count_file['page'] == aPage]
        if len(remOrigins)>0:
            entry = remOrigins.iloc[0]
            return entry.page.strip(), entry.source_url.strip()
        else:
            # This means all origins of aPage have been annotated, get another page
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
    else:
        # This will only be used when a user logs in
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

    entry = s_p.loc[s_p['page'] == page]
    entry = entry.iloc[0]
    return entry.page.strip(), entry.source_url.strip()

@app.route('/', methods=['GET', 'POST'])
def home():
    print("GOT INTO INDEX")
    """ Session control"""
    if not session.get('logged_in'):
        return render_template("index.html")
    else:
        name = session.get('username')
        if request.method == 'POST':
            op = request.form.get('op')
            if op:
                if op in ['1', '2', '3', '4']:
                    save_annotation(session.get('claim'),session.get('origin'), op, name)
                    c_url, o_url = get_least_annotated_page(name, session['claim'])
            else:
                c_url = session['claim']
                o_url = session['origin']
        else:
            c_url, o_url = get_least_annotated_page(name)
        browser.get(c_url)
        c_body = browser.page_source
        
        injectionPoint=c_body.split("</body>")
        jqueryCode='<script src="https://code.jquery.com/jquery-3.4.1.js" integrity="sha256-WpOohJOqMqqyKL9FccASB9O0KwACQJpFTUBLTYOVvVU=" crossorigin="anonymous"></script>'
        jqEvnt='<script> $("a").on("click", function(e){ e.preventDefault(); if(e.target.href){ let link = e.target.href; $.ajax({ url: "/newOrigin", data: {"link":link}, type: "POST", success: function(response) { parent.document.getElementById("oframe").srcdoc=response.site; parent.document.getElementById("oLink").href=response.link;}, error: function(error) { console.log(error);} }); }}); </script></body>'
        c_body=injectionPoint[0]+jqueryCode+jqEvnt+injectionPoint[1]
        
        browser.get(o_url)
        o_body = browser.page_source
        session['claim'] = c_url
        session['origin'] = o_url
        return render_template('index.html', t1=c_body, t2=o_body, t3=c_url, t4=o_url)


@app.route('/login', methods=['GET', 'POST'])
def login():
    print("GOT INTO LOGIN")
    if request.method == 'GET':
        return render_template('login.html')
    else:
        name = request.form['username']
        passw = request.form['password']
        try:
            data = User.query.filter_by(username=name, password=passw).first()
            if data is not None:
                session['logged_in'] = True
                session['username'] = name
                return redirect(url_for('home'))
            else:
                return 'Wrong username or password.'
        except:
            return 'Error at login'


@app.route('/register', methods=['GET', 'POST'])
def register():
    print("GOT INTO REGISTER")
    if request.method == 'POST':
        data = User.query.filter_by(username = request.form['username']).first()
        if data is None:
            new_user = User(username=request.form['username'], password=request.form['password'])
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('home'))
        else:
            return 'Username already in use'
    else: 
        return render_template('register.html')


@app.route("/logout")
def logout():
    """Logout Form"""
    session['logged_in'] = False
    return redirect(url_for('home'))


if __name__ == '__main__':
    db.create_all()


@app.route('/newOrigin', methods=['POST'])
def newOrigin():
    browser.get(request.form["link"])
    origin = browser.page_source
    return jsonify({'site': origin, 'link': request.form["link"]})
