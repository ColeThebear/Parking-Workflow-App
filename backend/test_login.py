import requests

# Test login endpoint
url = "http://localhost:8000/auth/login"
data = {"email": "student1@suny.edu", "password": "Test123!"}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")