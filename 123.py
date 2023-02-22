import requests


url = f"http://127.0.0.1:8000/api/tariff/Эконом"
response = requests.get(url)
print(response.text)
