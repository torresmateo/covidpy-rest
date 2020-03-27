from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from datetime import datetime
import pandas as pd
import os
from scipy import optimize


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
    res = []
    for i,r in covpy.iterrows():
        res.append({
            'date':r.date.strftime('%Y-%m-%d'), 
            'cases':int(r.cases), 
            'deaths':int(r.deaths), 
            'tests':int(r.tests), 
            'recovered':int(r.recovered),
            #'cum_cases':int(r.cum_cases),
            #'cum_deaths':int(r.cum_deaths),
            #'cum_tested':int(r.cum_tests),
            'total_male':int(r.total_male),
            'total_female':int(r.total_female)
        })
    return jsonify(res), 200


@app.route('/expanded')
@cross_origin()
def expanded():
    res = []
    for i,r in covpy.iterrows():
        res.append({
            'date':r.date.strftime('%Y-%m-%d'), 
            'cases':int(r.cases), 
            'deaths':int(r.deaths), 
            'tests':int(r.tests), 
            'recovered':int(r.recovered),
            'cum_cases':int(r.cum_cases),
            'cum_deaths':int(r.cum_deaths),
            'cum_tested':int(r.cum_tests),
            'total_male':int(r.total_male),
            'total_female':int(r.total_female)
        })
    return jsonify(res), 200

def logistic_function(x: float, a: float, b: float, c: float):
    ''' 1 / (1 + e^-x) '''
    return a / (1.0 + np.exp(-b * (x - c)))

@app.route('/logistic')
@cross_origin()
def logistic_prediction():
    country = covpy[['date','cum_cases']].set_index('date')
    X, y = list(range(len(country))), country['cum_cases'].tolist()
    # Estimate model parameters
    params, _ = optimize.curve_fit(logistic_function, X, y, maxfev=int(1E5), p0=[max(y), 1, np.median(X)])

    FUTURE_DAYS = 2

    # Append N new days to our indices
    date_format = '%Y-%m-%d'
    date_range = [date for date in country.index]
    for _ in range(FUTURE_DAYS): date_range.append(date_range[-1] + datetime.timedelta(days=1))
    date_range = [datetime.datetime.strftime(date, date_format) for date in date_range]

    projected = [0] * len(X) + [logistic_function(x, *params) for x in range(len(X), len(X) + FUTURE_DAYS)]
    projected = pd.Series(projected, index=date_range, name='Projected')
    df_ = pd.DataFrame({'Confirmed': country['cum_cases'], 'Projected': projected})
    estimate = [logistic_function(x, *params) for x in range(len(date_range))]
    return jsonify({
            'confirmed': df_.Confirmed.fillna(0).to_list(), 
            'projected': projected,
            'estimate':estimate,
            'dates':date_range
        }), 200

if __name__ == "__main__":
    app.run()