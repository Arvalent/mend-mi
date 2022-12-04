import requests

BASE = "http://127.0.0.1:5000/"

obj = {"name": "lucas", "city": "Fribourg", "addr": "avenue", "pin": 222}
response = requests.post(BASE + "new_post", json=obj)
print(response.json())
