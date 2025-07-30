import requests
import json

# Test deletion logic specifically
base_url = "https://b7cbdad9-3b55-4681-afe7-7771b233d6c0.preview.emergentagent.com"
api_url = f"{base_url}/api"

# Login first
login_data = {
    "email": "admin@schmitz-intralogistik.de",
    "password": "admin123"
}

response = requests.post(f"{api_url}/auth/login", json=login_data)
token = response.json()['access_token']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

print("🔍 Debugging Deletion Logic")
print("=" * 50)

# Create a test timesheet
timesheet_data = {
    "week_start": "2025-07-21",
    "entries": [{
        "date": "2025-07-21",
        "start_time": "08:00",
        "end_time": "16:00",
        "break_minutes": 30,
        "tasks": "Debug test",
        "customer_project": "Debug project",
        "location": "Debug location"
    }]
}

print("\n1. Creating test timesheet...")
response = requests.post(f"{api_url}/timesheets", json=timesheet_data, headers=headers)
timesheet = response.json()
timesheet_id = timesheet['id']
print(f"   Created timesheet: {timesheet_id}")
print(f"   Status: {timesheet.get('status', 'unknown')}")

# Try to send email to mark as sent
print(f"\n2. Attempting to mark timesheet as sent...")
response = requests.post(f"{api_url}/timesheets/{timesheet_id}/send-email", headers=headers)
print(f"   Send email response: {response.status_code}")

# Check timesheet status after send attempt
print(f"\n3. Checking timesheet status after send attempt...")
response = requests.get(f"{api_url}/timesheets", headers=headers)
timesheets = response.json()
for ts in timesheets:
    if ts['id'] == timesheet_id:
        print(f"   Timesheet status: {ts.get('status', 'unknown')}")
        break

# Try to delete the timesheet
print(f"\n4. Attempting to delete timesheet...")
response = requests.delete(f"{api_url}/timesheets/{timesheet_id}", headers=headers)
print(f"   Delete response: {response.status_code}")
if response.content:
    try:
        print(f"   Delete response body: {response.json()}")
    except:
        print(f"   Delete response text: {response.text}")

# Check if timesheet still exists
print(f"\n5. Checking if timesheet still exists...")
response = requests.get(f"{api_url}/timesheets", headers=headers)
timesheets = response.json()
still_exists = any(ts['id'] == timesheet_id for ts in timesheets)
print(f"   Timesheet still exists: {still_exists}")