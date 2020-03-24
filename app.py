from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from datetime import datetime
import pandas as pd
import os

data = []
skip = True
for line in open('covidpy.csv'):
    if skip:
        skip = False
        continue
    date, cases, deaths, tests, recoveries = line.strip().split(',')
    data.append({
        'date':date, 
        'cases':int(cases), 
        'deaths':int(deaths), 
        'tests':int(tests), 
        'recoveries':int(recoveries)
    })

covpy = pd.read_csv('../data/real_data_py.csv', parse_dates=[0], index_col='date')
covpy = covpy.resample('D').asfreq().fillna(0)
covpy['cum_cases'] = covpy['new_cases'].cumsum()
covpy['cum_deaths'] = covpy['new_deaths'].cumsum()
covpy['cum_tested'] = covpy['tested'].cumsum()
covpy['cum_recovered'] = covpy['recovered'].cumsum()
covpy.reset_index(inplace=True)


app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/')
@cross_origin()
def main():
    return jsonify(data), 200


@app.route('/expanded')
@cross_origin()
def recharts():
    res = []
    for i,r in covpy.iterrows():
        #'date', 'new_cases', 'new_deaths', 'tested', 'recovered', 'cum_cases','cum_deaths', 'cum_tested'
        res.append({
            'date':r.date.strftime('%Y-%m-%d'), 
            'cases':int(r.new_cases), 
            'deaths':int(r.new_deaths), 
            'tests':int(r.tested), 
            'recoveries':int(r,recovered),
            'cum_cases':int(r.cum_cases),
            'cum_deaths':int(r.cum_deaths),
            'cum_tested':int(r.cum_tested),
        })
    return 

if __name__ == "__main__":
    app.run()