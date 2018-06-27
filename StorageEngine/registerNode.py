import requests
import json

r = requests.post('http://localhost:5001/register', json={"nodename": "Node11", "nodeaddress": "localhost:5111"})
r.status_code
#r.json()