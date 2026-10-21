
import requests

BASE_URL = "http://127.0.0.1:5000"

# A session automatically keeps cookies between requests
client = requests.Session()

# Test signup
signup_data = {
    "username": "bob",
    "email": "bob@example.com",
    "password": "ExamplePassword123!"
}

response = client.post(
    f"{BASE_URL}/api/signup",
    json=signup_data
)

print("SIGNUP")
print("Status:", response.status_code)
print("Response:", response.json())

# Test login
login_data = {
    "email": "bob@example.com",
    "password": "ExamplePassword123!"
}

response = client.post(
    f"{BASE_URL}/api/login",
    json=login_data
)

print("\nLOGIN")
print("Status:", response.status_code)
print("Response:", response.json())

# Test whether the login session is remembered
response = client.get(f"{BASE_URL}/api/me")

print("\nSESSION CHECK")
print("Status:", response.status_code)
print("Response:", response.json())

# Test logout
response = client.post(f"{BASE_URL}/api/logout")

print("\nLOGOUT")
print("Status:", response.status_code)
print("Response:", response.json())

# Check that the session has ended
response = client.get(f"{BASE_URL}/api/me")

print("\nAFTER LOGOUT")
print("Status:", response.status_code)
print("Response:", response.json())
