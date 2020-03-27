from flask import Flask, request, send_from_directory
from flask_cors import CORS, cross_origin
from scripts import script as scripts
scripts.run()


app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/<path:path>')
@cross_origin()
def send_js(path):
    return send_from_directory('data', path+'.json')


if __name__ == "__main__":
    app.run()
