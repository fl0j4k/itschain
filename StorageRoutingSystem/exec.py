from flask import Flask, render_template, request, send_file
from gevent.pywsgi import WSGIServer
import os
import sqlite3 as db
from threading import Thread
from time import sleep
import uuid
from flask.json import jsonify
import configparser
import sqlhandler

app = Flask(__name__)
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
config = configparser.ConfigParser()
config.read(os.path.join(__location__, 'config.cfg'))
DATABASE = config['DATABASE']['DB_FILE']

def start_thread():
    def state_checker():
        while 1:
            if (os.path.isfile(__location__ + DATABASE)):
                print("***SRS: Checking connection states.")
                dbconn = db.connect(__location__ + DATABASE)
                with dbconn:
                    cur = dbconn.cursor()
                    cur.execute("DELETE FROM connected WHERE handshaketime <= datetime('now', '-10 minutes')")
                    dbconn.commit()
                sleep(300)
            else:
                print("***SRS: Setting up database . . .")
                dbconn = db.connect(__location__ + DATABASE)
                sqlhandler.installDatabase(dbconn)
                print("***SRS: Database setup finished.")

    thread = Thread(target=state_checker)
    thread.start()

@app.route('/heartbeat', methods = ['POST', 'GET'])
def heartbeat():
    giveback = 'FAILED!'
    if request.method == 'POST':
        inputvalues = request.form
        nodename = inputvalues['nodename']
        nodeaddr = inputvalues['nodeaddr']

        dbconn = db.connect(__location__ + DATABASE)
        with dbconn:
            cur = dbconn.cursor()
            cur.execute("SELECT nodename FROM connected")
            connected = cur.fetchall()
            for node in connected:
                if(str(node[0]) == nodename):
                    cur.execute("UPDATE connected SET handshaketime=datetime('now') WHERE nodename=?", (nodename,))
                    giveback = 'SUCCESS'

            if giveback != 'SUCCESS':
                cur.execute("SELECT * FROM nodes WHERE connectaddr = ?", (nodeaddr,))
                rows = cur.fetchall()
                for row in rows:
                    print(row)
                if(len(rows) == 1):
                    cur.execute("INSERT INTO connected VALUES(?,?,datetime('now'))", (nodename, nodeaddr))
                    giveback = 'SUCCESS - UPDATING!'

    return giveback

@app.route('/')
def index():
    dbconn = db.connect(__location__ + DATABASE)
    with dbconn:
        cur = dbconn.cursor()
        #cur.execute("INSERT INTO connected VALUES('Node1','localhost:5111',datetime('now', 'localtime'))")
        cur.execute("SELECT * FROM connected")
        dbconn.commit()
        rows = cur.fetchall()
        for row in rows:
            print(row)
    dbconn.close()
    return render_template("index.html", connected=rows)

@app.route('/new', methods = ['GET'])
def new(address=None):
    if request.method == 'GET':
        #inputvalues = request.form
        dbconn = db.connect(__location__ + DATABASE)
        #***
        #Store file
        #***
        #file = request.files['file']
        #if file:
        #    filename = secure_filename(file.filename)
        address = str(uuid.uuid4())
        with dbconn:
            cur = dbconn.cursor()
            cur.execute("SELECT * FROM lastid")
            lastDataId = cur.fetchone()[0]
            nodecounter = 0

            cur.execute("SELECT * FROM nodes")
            rows = cur.fetchall()
            for row in rows:
                print(row)

            cur.execute("SELECT id FROM connected INNER JOIN nodes on connected.nodename = nodes.name")
            connected = cur.fetchall()
            for node in connected:
                if nodecounter < 3:
                    cur.execute("INSERT INTO assignednodes VALUES(?, ? ,?)",
                                (1, lastDataId + 1, node[0]))
                    nodecounter += 1
                else:
                    continue

            cur.execute("INSERT INTO data VALUES(?,?)", (lastDataId + 1, address))

            cur.execute("UPDATE lastid SET dataid=? WHERE dataid=?", (lastDataId+1, lastDataId))
            #cur.execute("INSERT INTO nodes VALUES(?,'Node1', 'http://localhost:5111')", (cur.fetchone()[0] + 1,))


        print("Address: ", address)

        cur.execute("SELECT * FROM data")
        rows = cur.fetchall()
        for row in rows:
            print(row)

        cur.execute("SELECT * FROM nodes")
        rows = cur.fetchall()
        for row in rows:
            print(row)

    return address

@app.route('/register', methods = ['POST', 'GET'])
def register():
    giveback = "FAILED!"
    if request.method == 'POST':
        inputvalues = request.form
        nodename = inputvalues["nodename"]
        nodeaddress = inputvalues["nodeaddr"]


        dbconn = db.connect(__location__ + DATABASE)
        cur = dbconn.cursor()

        cur.execute("SELECT * FROM nodes WHERE connectaddr = ?", (nodeaddress,))
        rows = cur.fetchall()
        if(len(rows) == 0):
            cur.execute("SELECT nodesid FROM lastid")
            id = cur.fetchone()[0]
            id += 1
            with dbconn:
                cur = dbconn.cursor()
                cur.execute("INSERT INTO nodes VALUES(?,?,?)",(id,nodename, nodeaddress))
                cur.execute("UPDATE lastid SET nodesid=? WHERE nodesid=?", (id, id-1))
            giveback = "SUCCESS adding " + nodename
        else:
            giveback = "FAILED - Node with address already registered!"
    return giveback

@app.route('/get/<address>')
def get(address=None):
    dbconn = db.connect(__location__ + DATABASE)
    cur = dbconn.cursor()

    cur.execute(
        "SELECT nodes.connectaddr, nodes.name FROM ((nodes LEFT JOIN assignednodes ON nodes.id = assignednodes.nodeid) INNER JOIN data on data.id = assignednodes.dataid ) INNER JOIN connected ON connected.nodename = nodes.name WHERE data.address = ? ",
        (address,))
    rows = cur.fetchall()
    for row in rows:
        print(row)

    #cur.execute("SELECT nodes.connectaddr, assignednodes.dataid, data.address FROM (nodes INNER JOIN assignednodes ON nodes.id = assignednodes.nodeid) INNER JOIN data on data.id = assignednodes.dataid WHERE data.address = ? ", (address,))
    #cur.execute("SELECT nodes.connectaddr,nodes.id, assignednodes.dataid FROM (assignednodes LEFT JOIN nodes ON nodes.id = assignednodes.nodeid)")
    return jsonify({'nodes': rows})

@app.route('/remove')
def remove():
    return 'Hello World!'


if __name__ == '__main__':
    start_thread()
    #app.run(host="0.0.0.0", port=8547)
    http_server = WSGIServer(('0.0.0.0', 9916), app)
    http_server.serve_forever()
    #thread.join()
