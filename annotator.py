from flask import Flask, flash, request, Response, url_for, redirect, session, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from app import app
from app import db
from app.models import User
import os
import sys
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


cwd = os.path.abspath(os.path.dirname(__file__))

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920x1080")
chrome_driver = cwd+"/chromedriver"

browser = webdriver.Chrome(
    chrome_options=chrome_options, executable_path=chrome_driver)

res_header = ["page", "claim", "claim_label", "tags", "claim_source_domain", "claim_source_url",
              "date_check", "source_body", "date_fake", "dataset", "value", "annotator_name"]
samples_path = cwd+"/data/samples.csv"
results_path = cwd+"/data/results/"
count_path = cwd+"/data/count.csv"
db.create_all()


def increase_page_annotation_count(page, origin):
    count_file = pd.read_csv(count_path, sep=',')
    count_file.loc[(count_file['page'] == page)&(count_file['claim_source_url'] == origin), 'count'] += 1
    count_file.to_csv(count_path, sep=',', index=False)


def save_annotation(page, origin, value, name):
    # Read samples file
    s_p = pd.read_csv(samples_path, sep='\t')
    entry = s_p.loc[(s_p["page"] == page) & (s_p["claim_source_url"] == origin)]
    n_entry = entry.values.tolist()[0]
    n_entry.extend([value, name])
    results_filename = results_path+name+".csv"
    if os.path.exists(results_filename):
        results = pd.read_csv(results_filename, sep=',')
    else:
        results = pd.DataFrame(columns=res_header)
    results.loc[len(results)] = n_entry
    results.to_csv(results_filename, sep=',', index=False)
    # Keeps track of how many times page was annotated
    increase_page_annotation_count(page, origin)


def get_least_annotated_page(name,aPage=None):
    # Creates a list of pages that have been already annotated by the current annotator
    results_filename = results_path+name+".csv"
    if os.path.exists(results_filename):
        results = pd.read_csv(results_filename, sep=',')
        done_by_annotator = (results["page"]+results["claim_source_url"]).unique()
    else:
        done_by_annotator = []
    
    #Print number of annotated pages and total number of pages
    s_p = pd.read_csv(samples_path, sep='\t')
    print("done: ", len(done_by_annotator),
          " | total: ", len(s_p))
    if len(done_by_annotator) == len(s_p.page.unique()):
        return "Last annotation done! Thank you!", "Last annotation done! Thank you!", "Last annotation done! Thank you!", "Last annotation done! Thank you!"

    # Creates or reads countfile:
    if os.path.exists(count_path):
        count_file = pd.read_csv(count_path, sep=',').sample(frac=1)
    else:
        count_file = s_p[['page','claim_source_url']].copy()
        count_file['count'] = 0
        count_file.to_csv(count_path, sep=',', index=False)
        
    #Get pages not done by current annotator
    count_file = count_file.loc[~(count_file['page']+count_file['claim_source_url']).isin(done_by_annotator)]
    
    #Check if there are, and retrieve, other origins of aPage 
    if aPage is not None:
        remOrigins = count_file.loc[count_file['page'] == aPage]
        if len(remOrigins)>0:
            page = remOrigins.iloc[0]['claim_source_url']
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
    return entry.page.strip(), \
        entry.claim.strip(), \
        entry.source_body.strip(), \
        entry.claim_source_url.strip()


@app.route('/', methods=['GET', 'POST'])
def home():
    """ Session control"""
    if not session.get('logged_in'):
        return render_template("index.html")
    else:
        name = session.get('username')
        if request.method == 'POST':
            op = request.form.get('op')
            if op:
                if op in ['1', '2', '3', '4']:
                    save_annotation(session.get('page'),session.get('origin'), op, name)
            page, claim, origin, o_url = get_least_annotated_page(name, session['page'])
            browser.get(page)
            claim = browser.page_source
            twoHalves_1=claim.split("</body>")
            newFunc='<script> $("a").on("click",function(e){ e.preventDefault(); if(e.target.href){ let link = e.target.href; $.ajax({ url: "/newOrigin", data: {"link":link}, type: "POST", success: function(response) { parent.document.getElementById("oframe").srcdoc=response.site;}, error: function(error) {console.log(error);} }); }});</script></body>'
            claim=twoHalves_1[0]+newFunc+twoHalves_1[1]
            browser.get(o_url)
            origin = browser.page_source
            session['page'] = page
            session['origin'] = o_url
            return render_template('index.html', t1=claim, t2=origin, t3=page, t4=o_url)

        page, claim, origin, o_url = get_least_annotated_page(name)
        browser.get(page)
        claim = browser.page_source
        twoHalves_1=claim.split("</body>")
        newFunc='<script> $("a").on("click",function(e){ e.preventDefault(); if(e.target.href){ let link = e.target.href; $.ajax({ url: "/newOrigin", data: {"link":link}, type: "POST", success: function(response) { parent.document.getElementById("oframe").srcdoc=response.site;}, error: function(error) {console.log(error);} }); }});</script></body>'
        claim=twoHalves_1[0]+newFunc+twoHalves_1[1]
        browser.get(o_url)
        origin = browser.page_source
        session['page'] = page
        session['origin'] = o_url
        return render_template('index.html', t1=claim, t2=origin, t3=page, t4=o_url)


@app.route('/login', methods=['GET', 'POST'])
def login():
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
    """Register Form"""
    if request.method == 'POST':
        new_user = User(
            username=request.form['username'], password=request.form['password'])
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('home'))
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
    return jsonify({'site': origin})
