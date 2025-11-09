import requests

url = "http://127.0.0.1:8000/login/"
payload = {
    "username": "admin@example.com",
    "password": "Added123%"
}
headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

response = requests.post(url, data=payload, headers=headers)

print("Status Code:", response.status_code)
print("Response:", response.text)
