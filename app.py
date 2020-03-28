from flask import Flask, request, send_from_directory
from flask_cors import CORS, cross_origin
from scripts import script as scripts
from threading import Timer

class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

def update_stuff():
    scripts.run()


app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/<path:path>')
@cross_origin()
def send_js(path):
    return send_from_directory('data', path+'.json')


if __name__ == "__main__":
    print('it started!')
    update_stuff()
    print('it updated stuff..creating timer')
    rt = RepeatedTimer(10 * 60, update_stuff)
    print(os.listdir('./data'))
    app.run()
