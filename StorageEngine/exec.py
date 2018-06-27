from flask import Flask, send_file, request, Response
from gevent.pywsgi import WSGIServer
from threading import Thread
from time import sleep
import os, io
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import base64
import configparser

app = Flask(__name__)
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
config = configparser.ConfigParser()
config.read(os.path.join(__location__, 'config.cfg'))

SRS_HOST = config['SRS']['HOST']
NODENAME = config['LOCAL']['NODENAME']
NODEADDR = config['LOCAL']['NODEADDR']
UPLOAD_FOLDER = config['LOCAL']['UPLOAD_FOLDER']
OS = config['LOCAL']['OS']
if OS == 'LNX' or OS == 'MAC':
    PATH_ESC = '/'
if OS == 'WIN':
    PATH_ESC = '\\'

def start_thread():
    def state_sender():
        while 1:
            try:
                print("***StorageEngine: Sending heartbeat. . . ")
                request = Request(SRS_HOST + "heartbeat", urlencode({'nodename': NODENAME, 'nodeaddr': NODEADDR}).encode())
                response = urlopen(request).read().decode()
                print("***StorageEngine: hearbeat ", response)
                if response == 'FAILED!':
                    print("***StorageEngine: Register at SRS . . . ")
                    request2 = Request(SRS_HOST + "register", urlencode({'nodename': NODENAME, 'nodeaddr': NODEADDR}).encode())
                    response2 = urlopen(request2).read().decode()
                    print("***StorageEngine: ", response2)

                    print("***StorageEngine: Sending heartbeat. . . ")
                    request3 = Request(SRS_HOST + "heartbeat", urlencode(
                        {'nodename': NODENAME, 'nodeaddr': NODEADDR}).encode())
                    response3 = urlopen(request3).read().decode()
                    print(response3)

                sleep(300)

            except Exception:
                print("Connection error. Retrying in 30sec.")
                sleep(30)


    thread = Thread(target=state_sender)
    thread.start()

@app.route('/alive/<address>/<filename>')
def alive(address=None, filename=None):
    dir = os.path.isdir(UPLOAD_FOLDER + address)
    file = os.path.exists(UPLOAD_FOLDER + address + PATH_ESC + filename)
    return 'HELLO' + '-' + str(dir) + '-' + str(file)

@app.route('/serve/<address>/<filename>')
def serve(address=None, filename=None):
    splittedFileName = filename.split(".")
    ext = splittedFileName[len(splittedFileName) - 1]

    if ext != "its":
        final_path = UPLOAD_FOLDER + address + PATH_ESC + filename
        return send_file(final_path, mimetype='image/jpg')
    else:
        final_path = UPLOAD_FOLDER + address + PATH_ESC + filename
        with open(final_path, 'rb') as fin:
           # data = io.BytesIO(fin.read())
            return send_file(
                io.BytesIO(fin.read()),
                attachment_filename=filename
            )

@app.route('/store/<address>', methods = ['POST', 'GET'])
def store(address=None):
    if request.method == 'POST':
        file = request.form['data']
        filename = request.form['filename']
        file = base64.b64decode(file)

        if not os.path.exists(UPLOAD_FOLDER + address):
            os.makedirs(UPLOAD_FOLDER+ address)

        filename = os.path.join(UPLOAD_FOLDER + address, filename)
        with open(filename, 'wb') as f:
            f.write(file)
        response = {'SUCCESS': 'SUCCESS'}
    return Response(response=response, status=200, mimetype="application/json")

if __name__ == '__main__':
    start_thread()
    #app.run(host="0.0.0.0", port=8548)
    http_server = WSGIServer(('0.0.0.0', 9908), app)
    http_server.serve_forever()
