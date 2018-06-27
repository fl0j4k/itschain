from flask import Flask, render_template, request, send_file,session, redirect
from web3 import Web3, HTTPProvider
from gevent.pywsgi import WSGIServer
import os
import pickle
import json as json_lib
import chainlogic.imageHandler as ci
import imglogic.featureExtractor as fext
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import base64
import hashlib
import datetime
from dateutil import relativedelta
from werkzeug.utils import secure_filename
import configparser
import requests, shutil
from random import randint

#**
# Configuration
#**

app = Flask(__name__)
app.secret_key = b'\xf2\xaf\xbaK\x12\x12\xa4\xd2\x02vK\xc5a\x04\x0br'

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
config = configparser.ConfigParser()
config.read(os.path.join(__location__, 'config.cfg'))

UPLOAD_FOLDER = config['DEFAULT']['TEMP_UPLOAD']
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMP_UPLOAD'] = config['DEFAULT']['TEMP_UPLOAD']
SRS_HOST = config['SRS']['HOST']
GETHNODE = config['WEB3']['GETHNODE']
COINBASE = config['WEB3']['COINBASE']
PASSW = config['WEB3']['PASSW']
INDEXSTORAGE = config['WEB3']['INDEXSTORAGE']

#**
# Method for the blockchain authentication process
#**
@app.route('/login', methods = ['POST', 'GET'])
def login():
    ethnode = GETHNODE
    status = "null"
    accounts = "null"
    hexcolor = "#bbb"
    connection = 1
    currentTime = datetime.datetime.now()
    if 'ethauthtime' in session:
        lastSession = session['ethauthtime'];
        tdiff = relativedelta.relativedelta(currentTime, lastSession)
    else:
        lastSession = datetime.datetime(2000, 1, 1, 1, 1, 1, 1)
        tdiff = relativedelta.relativedelta(currentTime, lastSession)
    if request.method == 'GET' and tdiff.minutes <= 10:
        hexcolor = "#39e600"
    if tdiff.minutes > 10:
        session['active'] = "false"

    if request.method == 'POST':
        inputvalues = request.form
        w3 = None
        if 'ethnode' in inputvalues:
            try:
                w3 = Web3(HTTPProvider(inputvalues['ethnode']))
                session['ethnode'] = inputvalues['ethnode']
                ethnode = session['ethnode']
                accounts = w3.eth.accounts
                print(accounts)
            except Exception:
                connection = 2
                ethnode = inputvalues['ethnode']

        else:
            try:
                w3 = Web3(HTTPProvider(session['ethnode']))
                resp = w3.personal.unlockAccount(w3.toChecksumAddress(inputvalues['ethaccount']), inputvalues['ethpass'])
                ethnode = session['ethnode']
                if resp == True:
                    status = "checked"
                    session['ethauthtime'] = datetime.datetime.now()
                    session['active'] = "true"
                    session['ethaccount'] = inputvalues['ethaccount']
                    session[inputvalues['ethaccount'][2:]] = base64.b64encode(inputvalues['ethpass'].encode('utf-8'))
                    hexcolor = "#39e600"

                else:
                    status = "failed"
                    hexcolor = "#bbb"
            except Exception:
                connection = 2
                ethnode = inputvalues['ethnode']

    return render_template("login.html", accounts=accounts, status=status, defaultnode=ethnode, hexcolor=hexcolor, connection=connection)


@app.route('/insert', methods = ['POST', 'GET'])
def insert():
    newaddr = "NULL"
    success = "NULL"
    currentTime = datetime.datetime.now()
    if 'ethauthtime' in session and session['active'] == "true":
        lastSession = session['ethauthtime'];
        tdiff = relativedelta.relativedelta(currentTime, lastSession)
    else:
        lastSession = datetime.datetime(2000, 1, 1, 1, 1, 1, 1)
        tdiff = relativedelta.relativedelta(currentTime, lastSession)

    if request.method == 'POST' and tdiff.minutes <= 10:
        inputvalues = request.form

        #***
        #Store file
        #***
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            r = Request(SRS_HOST + "new")
            storageaddress = urlopen(r).read().decode()

            r = Request(SRS_HOST + "get/" + storageaddress)
            hosts = urlopen(r).read().decode()
            decodedHosts = json_lib.loads(hosts)

            with open(app.config['UPLOAD_FOLDER'] + '/' + filename, "rb") as image_file:
                file = image_file.read()
            encoded_image = base64.b64encode(file)

            for host in decodedHosts['nodes']:
                try:
                    r = Request('http://' + host[0] + "/store/" + storageaddress,
                                      urlencode({'filename': filename, 'data': encoded_image}).encode())
                    r.add_header("Content-type", "application/x-www-form-urlencoded; charset=UTF-8")
                    json1 = urlopen(r).read().decode()
                    print(json1)
                except Exception as err:
                    print("Connection FAILED: {}".format(err))

            storagelink = 'itstore://' + storageaddress + '/' + filename

        #***
        # Extract features
        #***
        fextractor = fext.ImageEngine()
        allFeatures = fextractor.featureExtractor(app.config['UPLOAD_FOLDER'], filename)
        with open( 'storage/temp/' + filename + '.its', 'wb') as f:
            pickle.dump(allFeatures, f, protocol=pickle.DEFAULT_PROTOCOL)
        with open('storage/temp/' + filename + '.its', "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read())

        for host in decodedHosts['nodes']:
            try:
                r = Request('http://' + host[0] + "/store/" + storageaddress,
                              urlencode({'filename': filename + '.its', 'data': encoded_image}).encode())
                r.add_header("Content-type", "application/x-www-form-urlencoded; charset=UTF-8")
                json = urlopen(r).read().decode()
                print(json)
            except Exception as err:
                print("Connection FAILED: {}".format(err))

        fhash = hashlib.sha256();
        with open('storage/temp/' + filename + '.its', "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                fhash.update(chunk)
            fhash = fhash.hexdigest()


        #***
        #Insert to blockchain
        #***
        ih = ci.ImageHandler()
        newaddr = ih.insertHandler(inputvalues['imgname'], inputvalues['author'], allFeatures, filename, storagelink, fhash, session['ethaccount'], session[session['ethaccount'][2:]], session['ethnode'], INDEXSTORAGE)

        errmsg = newaddr.split("_")
        if(errmsg[0] == "ERROR"):
            success = "failed"
        else:
            success = newaddr
        print(newaddr)
        hexcolor = "#39e600"
        return render_template("insert.html", newaddr=newaddr, hexcolor=hexcolor, success=success)

    if tdiff.minutes > 10:
        session['active'] = "false"
        return redirect("/login", code=302)

    if request.method == 'GET' and tdiff.minutes <= 10:
        hexcolor = "#39e600"
        return render_template("insert.html", newaddr=newaddr, hexcolor=hexcolor, success=success)

@app.route('/')
def index():
    return render_template("index.html")


@app.route('/get/<address>')
def get(address=None):

    #**
    # Read imagedata from the blockchain
    #**
    contract_interface = {'abi': None, 'bin': None}
    w3 = Web3(HTTPProvider(GETHNODE))
    with open("chainlogic/contracts/itscontract_sol_ITSContract.abi", 'r') as abi_definition:
        contract_interface['abi'] = abi_definition.read()

    with open("chainlogic/contracts/itscontract_sol_ITSContract.bin", 'r') as abi_definition:
        contract_interface['bin'] = abi_definition.read()

    image_contract = w3.eth.contract(address=address,abi=contract_interface['abi'])

    chaindata = image_contract.functions.getImage().call()
    chaindata.append(address)

    if len(chaindata[5]) > 0 and chaindata[5].find("://") > -1:
        imgname = chaindata[5].split("://")
        imgname = imgname[1].split("/")
        hostaddress = imgname[0]
        imgname = imgname[1]

        chaindata.append(imgname)

    #**
    # Request storage nodes from StorageRoutingSystem
    #**
    try:
        request = Request(SRS_HOST + "get/" + hostaddress)
        hosts = urlopen(request).read().decode()
        decodedHosts = json_lib.loads(hosts)
    except Exception:
        print("Could not connect to SRS")

    #**
    # Select a random node and try to connect and request image data
    #**
    imghost = "http://"
    connattempt = 10
    while connattempt > 0:
        connattempt -= 1
        numhosts = len(decodedHosts['nodes'])-1
        hostid = randint(0, numhosts)
        host = decodedHosts['nodes'][hostid]
        try:
            print("Connecting to ", host[0])
            alivecheck = Request('http://' + host[0] + "/alive/" + hostaddress + "/" + imgname)
            response = urlopen(alivecheck).read().decode()
            if response == 'HELLO-True-True':
                imghost = 'http://' + host[0] + "/serve/" + hostaddress + "/" + imgname
                break
        except Exception as err:
            print("Connection FAILED: {}".format(err))

    chaindata.append(imghost)

    print("Output: ", chaindata)
    return render_template("details.html", chaindata=chaindata)


@app.route('/check', methods = ['POST', 'GET'])
@app.route('/check/<address>', methods = ['POST', 'GET'])
def check(address=None):
    matchresult = -1
    tempimgname = ''
    imghost = "http://"
    if request.method == 'POST':
        inputvalues = request.form

        #***
        #Store the uploaded image in the temp folder
        #***
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['TEMP_UPLOAD'], filename))

            # ***
            # Get storage infos of the selected image and request the stored feature file
            # ***
            storage = inputvalues['storage']
            if (len(storage) > 0 and storage.find("://") > -1):
                imgname = storage.split("://")
                imgname = imgname[1].split("/")
                hostaddress = imgname[0]
                imgname = imgname[1]
                tempimgname = filename

                try:
                    request2 = Request(SRS_HOST + "get/" + hostaddress)
                    hosts = urlopen(request2).read().decode()
                    decodedHosts = json_lib.loads(hosts)
                except Exception:
                    print("Could not connect to SRS")

            # **
            # Select one of the possible storage nodes and check if its alive
            # Request the stored feature file
            # **
            connattempt = 10
            while connattempt > 0:
                connattempt -= 1
                numhosts = len(decodedHosts['nodes']) - 1
                hostid = randint(0, numhosts)
                host = decodedHosts['nodes'][hostid]
                try:
                    alivecheck = Request('http://' + host[0] + "/alive/" + hostaddress + "/" + imgname)
                    response = urlopen(alivecheck).read().decode()
                    if (response == 'HELLO-True-True'):
                        imghost = 'http://' + host[0] + "/serve/" + hostaddress + "/" + imgname
                        break
                except Exception as err:
                    print("Connection FAILED: {}".format(err))

            #**
            # Receive the feature file and store it in the temp directory
            #**
            response = requests.get(imghost + '.its', stream=True)
            with open(os.path.join(app.config['TEMP_UPLOAD'], imgname + '.its'), 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
            del response

            #**
            # Make checksum test
            #**
            fhash = hashlib.sha256();
            chain_feature_hash = inputvalues['fhash']
            with open(os.path.join(app.config['TEMP_UPLOAD'], imgname + '.its'), "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    fhash.update(chunk)
                fhash = fhash.hexdigest()

            if chain_feature_hash == fhash:
                # **
                # Do the image matching of the selected and the uploaded one
                # **
                fextractor = fext.ImageEngine()
                matchresult = fextractor.imageMatcher(os.path.join(app.config['TEMP_UPLOAD'], imgname + '.its'),
                                                      app.config['TEMP_UPLOAD'] + '/' + filename)
            else:
                matchresult = "Failure: Integritycheck of imagefeatures was not successful!"

    #**
    # Read imagedata from the blockchain
    #**
    contract_interface = {'abi': None, 'bin': None}
    w3 = Web3(HTTPProvider(GETHNODE))
    with open("chainlogic/contracts/itscontract_sol_ITSContract.abi", 'r') as abi_definition:
        contract_interface['abi'] = abi_definition.read()

    with open("chainlogic/contracts/itscontract_sol_ITSContract.bin", 'r') as abi_definition:
        contract_interface['bin'] = abi_definition.read()

    image_contract = w3.eth.contract(address=address, abi=contract_interface['abi'])

    chaindata = image_contract.functions.getImage().call()
    chaindata.append(address)
    if (len(chaindata[5]) > 0 and chaindata[5].find("://") > -1):
        imgname = chaindata[5].split("://")
        imgname = imgname[1].split("/")
        hostaddress = imgname[0]
        imgname = imgname[1]

        chaindata.append(imgname)

        #**
        # Request storage nodes from StorageRoutingSystem
        #**
        try:
            request2 = Request(SRS_HOST + "get/" + hostaddress)
            hosts = urlopen(request2).read().decode()
            decodedHosts = json_lib.loads(hosts)
        except Exception:
            print("Could not connect to SRS")

    # **
    # Select one of the possible storage nodes and check if its alive
    # Request the stored feature file
    # **
    connattempt = 10
    while connattempt > 0:
        connattempt -= 1
        numhosts = len(decodedHosts['nodes'])-1
        hostid = randint(0, numhosts)
        host = decodedHosts['nodes'][hostid]
        try:
            alivecheck = Request('http://' + host[0] + "/alive/" + hostaddress + "/" + imgname)
            response = urlopen(alivecheck).read().decode()
            if(response == 'HELLO-True-True'):
                imghost = 'http://' + host[0] + "/serve/" + hostaddress + "/" + imgname
                break
        except Exception as err:
            print("Connection FAILED: {}".format(err))

    chaindata.append(imghost)


    return render_template("check.html", chaindata=chaindata, matchresult=matchresult, tempimgname=tempimgname )


#**
# Method for returning locally temporary stored images
# used by the check method for displaying the uploaded image
#**
@app.route('/imagehandler/<imgname>/<type>')
def imagehandler(imgname=None, type=None):
    full_uploadfolder_path = os.path.join(app.config['UPLOAD_FOLDER'], imgname)
    full_tempfolder_path = os.path.join(app.config['TEMP_UPLOAD'], imgname)
    final_path = ''
    if int(type) == 1:
        final_path = full_uploadfolder_path
    if int(type) == 2:
        final_path = full_tempfolder_path
    return send_file(final_path, mimetype='image/jpg')

#**
# Method for returning a list of all tracked images
#**
@app.route('/listall')
def listall():
    w3 = Web3(HTTPProvider(GETHNODE))
    w3.eth.defaultAccount = w3.toChecksumAddress(COINBASE);
    contract_interface = {'abi': None, 'bin': None}
    address = INDEXSTORAGE

    with open("chainlogic/contracts/ITSStorageIndex_sol_ITSStorageIndex.abi", 'r') as abi_definition:
        contract_interface['abi'] = abi_definition.read()

    with open("chainlogic/contracts/ITSStorageIndex_sol_ITSStorageIndex.bin", 'r') as abi_definition:
        contract_interface['bin'] = abi_definition.read()

    store_var_contract = w3.eth.contract(address=address, abi=contract_interface['abi'])
    idarray = store_var_contract.functions.getIndexList().call()



    with open("chainlogic/contracts/itscontract_sol_ITSContract.abi", 'r') as abi_definition:
        contract_interface['abi'] = abi_definition.read()

    with open("chainlogic/contracts/itscontract_sol_ITSContract.bin", 'r') as abi_definition:
        contract_interface['bin'] = abi_definition.read()

    itsobjects = []
    for n in idarray:
        allInfo = store_var_contract.functions.getAllInfo(n).call()
        address = allInfo[0]
        print("Output: ", address)

        image_contract = w3.eth.contract(
            address=address,
            abi=contract_interface['abi'])

        chaindata = image_contract.functions.getImage().call()
        for data in allInfo:
            chaindata.append(data)

        itsobjects.append(chaindata)


    return render_template("listall.html", itsobjects=itsobjects)


@app.route('/search', methods = ['POST', 'GET'])
def search():
    itsobjects = []
    if request.method == 'POST':
        inputvalues = request.form

        print(inputvalues['searchtext'])
        w3 = Web3(HTTPProvider(GETHNODE))
        w3.eth.defaultAccount = w3.toChecksumAddress(COINBASE);
        contract_interface = {'abi': None, 'bin': None}

        #***
        # Get all contract addresses from the Storage Contract
        #***
        address = INDEXSTORAGE
        with open("chainlogic/contracts/ITSStorageIndex_sol_ITSStorageIndex.abi", 'r') as f:
            contract_interface['abi'] = f.read()
        with open("chainlogic/contracts/ITSStorageIndex_sol_ITSStorageIndex.bin", 'r') as f:
            contract_interface['bin'] = f.read()

        storageIndex = w3.eth.contract(address=address, abi=contract_interface['abi'])
        idarray = storageIndex.functions.getIndexList().call()


        #***
        # Get each Image Contract
        #***
        with open("chainlogic/contracts/itscontract_sol_ITSContract.abi", 'r') as f:
            contract_interface['abi'] = f.read()
        with open("chainlogic/contracts/itscontract_sol_ITSContract.bin", 'r') as f:
            contract_interface['bin'] = f.read()

        for n in idarray:
            allInfo = storageIndex.functions.getAllInfo(n).call()
            address = allInfo[0]
            print("Output: ", address)

            image_contract = w3.eth.contract(address=address,abi=contract_interface['abi'])
            chaindata = image_contract.functions.getImage().call()
            for data in allInfo:
                chaindata.append(data)

            if(chaindata[int(inputvalues['searchtype'])] == inputvalues['searchtext']):
                itsobjects.append(chaindata)

    if request.method == 'GET':
        itsobjects.append(-1)

    return render_template("search.html", itsobjects=itsobjects)


if __name__ == "__main__":
    #app.run(host="0.0.0.0", port=8546)
    http_server = WSGIServer(('0.0.0.0', 8546), app)
    http_server.serve_forever()