import requests

resp = requests.get("http://ip-api.com/json")
print(resp.text)
