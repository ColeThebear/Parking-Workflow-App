import requests

# Test the my-sessions endpoint
url = "http://localhost:8000/parking/my-sessions"
headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5Iiwicm9sZSI6IlBBUktFUiIsImV4cCI6MTc3NDEzOTgzNX0.YMKQI0a5zVsZEsEVroJZc69oMaEP0e3aB-TPYDZl-HU"}

try:
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Sessions found: {len(data)}")
        for session in data:
            print(f"  {session['vehicle_plate']} - {session['zone']} - Active: {session['active']}")
    else:
        print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")