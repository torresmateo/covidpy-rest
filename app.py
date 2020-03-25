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
    date, cases, deaths, tests, recovered, total_male, total_female = line.strip().split(',')
    data.append({
        'date':date, 
        'cases':int(cases), 
        'deaths':int(deaths), 
        'tests':int(tests), 
        'recovered':int(recovered),
        'total_male':int(total_male),
        'total_female':int(total_female)
    })

covpy = pd.read_csv('covidpy.csv', parse_dates=[0], index_col='date')
covpy = covpy.resample('D').asfreq().fillna(0)
covpy['cum_cases'] = covpy['cases'].cumsum()
covpy['cum_deaths'] = covpy['deaths'].cumsum()
covpy['cum_tests'] = covpy['tests'].cumsum()
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
def expanded():
    res = []
    for i,r in covpy.iterrows():
        #'date', 'new_cases', 'new_deaths', 'tested', 'recovered', 'cum_cases','cum_deaths', 'cum_tested'
        res.append({
            'date':r.date.strftime('%Y-%m-%d'), 
            'cases':int(r.cases), 
            'deaths':int(r.deaths), 
            'tests':int(r.tests), 
            'recovered':int(r.recovered),
            'cum_cases':int(r.cum_cases),
            'cum_deaths':int(r.cum_deaths),
            'cum_tested':int(r.cum_tested),
            'total_male':int(r.total_male),
            'total_female':int(r.total_female)
        })
    return jsonify(res), 200

if __name__ == "__main__":
    app.run()