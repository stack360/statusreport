import requests
import simplejson as json
# input_data = {"username": "xx", "password": "huawei", "remember_me":"true"}
# json_str = json.dumps(input_data)
response = requests.get('http://192.168.255.58:9999/login/google')
data = response.json()
print data
