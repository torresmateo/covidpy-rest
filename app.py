from flask import Flask, jsonify, request
from datetime import datetime
import os

app = Flask(__name__)

@app.route('/')
def main():
    data = []
    skip = True
    for line in open('covidpy.csv')
        if skip:
            skip = False
            continue
        date, cases, deaths, tests, recoveries = line.split(',')
        data.append({
            'date':date, 
            'cases':cases, 
            'deaths':deaths, 
            'tests':tests, 
            'recoveries':recoveries
        })
    return jsonify(data), 200

# @app.route('/recharts')
# def recharts():
#     return 

if __name__ == "__main__":
    app.run()