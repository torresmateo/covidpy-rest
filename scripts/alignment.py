import pandas as pd
import numpy as np
import os
import json
import requests

CWD = os.path.dirname(os.path.abspath(__file__))
DATADIR = os.path.join(CWD, '../data')


def diff(a, b):
    long = a if a.shape[0] > b.shape[0] else b
    short = a if a.shape[0] <= b.shape[0] else b
    # we start by assuming that there is no delay (the short curve is to the right of the long one)
    offset_min = 0
    diff_min = np.inf
    # long pad to the left to accommodate for a very long previous overlap
    padded_long = np.zeros(long.shape[0] + short.shape[0])
    padded_long[-long.shape[0]:] = long
    long = padded_long
    for offset in range(long.shape[0] - short.shape[0] + 1):
        chunk = long[-(short.shape[0]):]
        if offset > 0:
            chunk = long[-(short.shape[0]+offset):-offset]
        diff = np.abs(chunk-short).sum()
        if diff_min > diff:
            diff_min = diff
            offset_min = offset
    return offset_min


def download_and_save():
    print('Gettind data from Johns Hopkins CSSE...')

    urls = ['https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv',
            'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv']
    for url in urls:
        r = requests.get(url)
        fname = os.path.join(DATADIR, url.split("/")[-1])
        with open(fname, 'wb') as f:
            f.write(r.content)

    print('formatting data for analysis...')
    conf_df = pd.read_csv(os.path.join(
        DATADIR, 'time_series_covid19_confirmed_global.csv'))
    deaths_df = pd.read_csv(os.path.join(
        DATADIR, 'time_series_covid19_deaths_global.csv'))

    dates = conf_df.columns[4:]

    conf_df_long = conf_df.melt(id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'],
                                value_vars=dates, var_name='Date', value_name='Confirmed')

    deaths_df_long = deaths_df.melt(id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'],
                                    value_vars=dates, var_name='Date', value_name='Deaths')

    # recv_df_long = recv_df.melt(id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'],
    #                            value_vars=dates, var_name='Date', value_name='Recovered')

    full_table = pd.concat(
        [conf_df_long, deaths_df_long['Deaths']], axis=1, sort=False)

    df = full_table[full_table['Province/State']
                    .str.contains(',') != True].copy()
    # df.to_csv('covid_19_clean_complete.csv', index=False)
    return df


def align(df):
    df['Date'] = df['Date'].astype('datetime64[ns]')
    df['country_region'] = df['Country/Region'] + ' ' + \
        df['Province/State'].fillna('').astype(str)
    df['country_region'] = df.country_region.str.strip()

    countries_with_region = df[~df['Province/State'].isna()
                               ]['Country/Region'].unique()
    for c in countries_with_region:
        reg = df[df['Country/Region'] == c]
        reg_confirmed = reg[['Confirmed', 'Date']].groupby(
            'Date').sum().reset_index().copy()
        reg_deaths = reg[['Deaths', 'Date']].groupby(
            'Date').sum().reset_index().copy()
        reg_new = reg_confirmed.copy()
        reg_new['Province/State'] = 'combined'
        reg_new['Country/Region'] = c
        reg_new['Confirmed'] = reg_confirmed.Confirmed
        reg_new['Deaths'] = reg_deaths.Deaths
        reg_new['country_region'] = f'{c}'
        reg_new['Lat'] = reg['Lat'].to_numpy()[0]
        reg_new['Long'] = reg['Long'].to_numpy()[0]
        df = df.append(reg_new)

    print('Calculating alignment...')

    south_america = ['Argentina', 'Uruguay', 'Chile', 'Bolivia', 'Paraguay', 'Brazil',
                     'Ecuador', 'Colombia', 'Venezuela', 'Peru', 'Guyana', 'Suriname', 'French Guiana']

    sp_names = {
        'Argentina': 'Argentina',
        'Uruguay': 'Uruguay',
        'Chile': 'Chile',
        'Bolivia': 'Bolivia',
        'Paraguay': 'Paraguay',
        'Brazil': 'Brasil',
        'Ecuador': 'Ecuador',
        'Colombia': 'Colombia',
        'Venezuela': 'Venezuela',
        'Peru': 'Perú',
        'Guyana': 'Guyana',
        'Suriname': 'Surinam',
        'French Guiana': 'Guyana Francesa'}

    br_y = df[(df['Country/Region'] == 'Brazil')].Confirmed.to_numpy()
    X = np.array(list(range(br_y.shape[0])))

    # to be made into a json
    data = {
        'ref_country': 'Brazil',  # TODO: pick the reference country programmatically
        'country_data': [
            {'name': 'Brazil', 'offset': 0, 'data': [{'x': int(X[i]), 'y':int(
                br_y[i])} for i in range(br_y.shape[0]) if (X[i] > 0) and (br_y[i] >= 1)]}
        ]
    }

    for c in south_america:
        if c in ['Brazil']:
            continue
        df_c = df[(df['country_region'] == c)].sort_values('Date')
        y = df_c.Confirmed.to_numpy()
        if y.shape[0] > 0:
            X = np.array(list(range(df_c.shape[0])))
            y_data = y[y > 0]
            delta = diff(y_data, br_y)
            data['country_data'].append(
                {'name': sp_names[c], 'offset': delta, 'data': [{'x': int(
                    X[i] - delta), 'y':int(y[i])} for i in range(y.shape[0]) if (X[i] - delta > 0) and (y[i] >= 1)]}
            )
    return data


def run():
    df = download_and_save()
    data = align(df)

    print('saving data...')
    json.dump(data, open(os.path.join(DATADIR, 'alignment.json'), 'w'))
    print('done')


if __name__ == "__main__":
    run()
