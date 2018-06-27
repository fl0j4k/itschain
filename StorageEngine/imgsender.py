import requests
import json
import cv2
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import base64

addr = 'http://localhost:5111'
test_url = addr + '/storage/asdfjkl123456'


with open('storage/0xDa38356a5332e2245714eCD7B24fB11762C8551F/maxresdefault.its', "rb") as image_file:
    encoded_image = base64.b64encode(image_file.read())

request = Request("http://localhost:5111/store/asdfjkl123456", urlencode({'filename': 'maxresdefault.its', 'data': encoded_image}).encode())
request.add_header("Content-type", "application/x-www-form-urlencoded; charset=UTF-8")
json = urlopen(request).read().decode()
print(json)