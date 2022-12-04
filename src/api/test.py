import requests

BASE = "http://127.0.0.1:5000/"

response = requests.put(BASE + "video/2", {'name': 'test', 'likes': 200, 'views':200})
print(response.json())