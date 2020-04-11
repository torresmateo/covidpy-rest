from datetime import datetime, timedelta
import pandas as pd
import os
from scipy import optimize
import numpy as np
import json

CWD = os.path.dirname(os.path.abspath(__file__))
DATADIR = os.path.join(CWD, '../data')


def run():
    # load the Paraguay dataset from MSPBS
    covpy = pd.read_csv(os.path.join(DATADIR, 'covidpy.csv'),
                        parse_dates=[0], index_col='date')
    covpy = covpy.resample('D').asfreq().fillna(0)
    covpy['cum_cases'] = covpy['cases'].cumsum()
    covpy['cum_deaths'] = covpy['deaths'].cumsum()
    covpy['cum_tests'] = covpy['tests'].cumsum()
    covpy['cum_recovered'] = covpy['recovered'].cumsum()
    covpy.reset_index(inplace=True)

    # plain data

    plain_data = []
    for i, r in covpy.iterrows():
        plain_data.append({
            'date': r.date.strftime('%Y-%m-%d'),
            'cases': int(r.cases),
            'deaths': int(r.deaths),
            'tests': int(r.tests),
            'recovered': int(r.recovered),
            'total_male': int(r.total_male),
            'total_female': int(r.total_female)
        })

    json.dump(plain_data, open(os.path.join(DATADIR, 'raw.json'), 'w'))

    # expanded

    expanded_data = []
    for i, r in covpy.iterrows():
        expanded_data.append({
            'date': r.date.strftime('%Y-%m-%d'),
            'cases': int(r.cases),
            'deaths': int(r.deaths),
            'tests': int(r.tests),
            'recovered': int(r.recovered),
            'cum_cases': int(r.cum_cases),
            'cum_deaths': int(r.cum_deaths),
            'cum_tested': int(r.cum_tests),
            'cum_recovered': int(r.cum_recovered),
            'total_male': int(r.total_male),
            'total_female': int(r.total_female)
        })

    # dump json
    json.dump(expanded_data, open(os.path.join(DATADIR, 'expanded.json'), 'w'))

    # logistic prediction

    FUTURE_DAYS = 2

    def logistic_function(x: float, a: float, b: float, c: float):
        ''' 1 / (1 + e^-x) '''
        return a / (1.0 + np.exp(-b * (x - c)))

    country = covpy[['date', 'cum_cases']].set_index('date')
    X, y = list(range(len(country))), country['cum_cases'].tolist()
    # Estimate model parameters
    params, _ = optimize.curve_fit(logistic_function, X, y, maxfev=int(1E5), p0=[
        max(y), 1, np.median(X)])
    date_format = '%Y-%m-%d'
    date_range = [date for date in country.index]
    for _ in range(FUTURE_DAYS):
        date_range.append(date_range[-1] + timedelta(days=1))
    date_range = [datetime.strftime(date, date_format) for date in date_range]
    projected = [0] * len(X) + [logistic_function(x, *params)
                                for x in range(len(X), len(X) + FUTURE_DAYS)]
    projected = pd.Series(projected, index=date_range, name='Projected')
    df_ = pd.DataFrame(
        {'Confirmed': country['cum_cases'], 'Projected': projected})
    estimate = [logistic_function(x, *params) for x in range(len(date_range))]
    # save to json
    logistic_prediction = {
        'confirmed': df_.Confirmed.fillna(0).to_list(),
        'projected': projected.fillna(0).astype(int).to_list(),
        'estimate': estimate,
        'dates': date_range
    }

    json.dump(logistic_prediction, open(
        os.path.join(DATADIR, 'logistic.json'), 'w'))


if __name__ == "__main__":
    run()
