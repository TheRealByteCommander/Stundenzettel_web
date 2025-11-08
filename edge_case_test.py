import requests
import json
from datetime import datetime, timedelta

# Test edge cases for Monday date bug
base_url = "http://localhost:8000"
api_url = f"{base_url}/api"

# Login first
login_data = {
    "email": "admin@schmitz-intralogistik.de",
    "password": "admin123"
}

response = requests.post(f"{api_url}/auth/login", json=login_data)
token = response.json()['access_token']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

print("🔍 Testing Edge Cases for Monday Date Bug")
print("=" * 60)

# Test cases that cross month boundaries
edge_cases = [
    ("2025-06-30", "2025-07-06"),  # Monday June 30 -> Sunday July 6 (crosses month)
    ("2025-03-31", "2025-04-06"),  # Monday March 31 -> Sunday April 6 (crosses month)
    ("2025-12-29", "2026-01-04"),  # Monday Dec 29, 2025 -> Sunday Jan 4, 2026 (crosses year)
    ("2025-02-24", "2025-03-02"),  # Monday Feb 24 -> Sunday March 2 (February edge)
]

all_passed = True

for week_start, expected_week_end in edge_cases:
    print(f"\n📅 Testing Monday: {week_start} -> Expected Sunday: {expected_week_end}")
    
    # Create a simple timesheet entry
    entries = [{
        "date": week_start,
        "start_time": "08:00",
        "end_time": "17:00",
        "break_minutes": 30,
        "tasks": "Edge case testing",
        "customer_project": "Quality Assurance",
        "location": "Machern"
    }]
    
    timesheet_data = {
        "week_start": week_start,
        "entries": entries
    }
    
    response = requests.post(f"{api_url}/timesheets", json=timesheet_data, headers=headers)
    
    if response.status_code == 200:
        timesheet = response.json()
        actual_week_start = timesheet.get('week_start')
        actual_week_end = timesheet.get('week_end')
        
        if actual_week_start == week_start and actual_week_end == expected_week_end:
            print(f"   ✅ PASSED: week_start={actual_week_start}, week_end={actual_week_end}")
        else:
            print(f"   ❌ FAILED: Expected week_start={week_start}, week_end={expected_week_end}")
            print(f"              Got week_start={actual_week_start}, week_end={actual_week_end}")
            all_passed = False
    else:
        print(f"   ❌ FAILED: HTTP {response.status_code} - {response.text}")
        all_passed = False

print(f"\n{'='*60}")
if all_passed:
    print("🎉 All edge case tests PASSED!")
else:
    print("⚠️  Some edge case tests FAILED!")

print(f"\n🔍 Testing Authentication Edge Cases")
print("=" * 60)

# Test without authentication
print("\n📋 Testing API without authentication...")
response = requests.get(f"{api_url}/timesheets")
if response.status_code == 403:
    print("   ✅ Correctly rejected unauthenticated request")
else:
    print(f"   ❌ Expected 403, got {response.status_code}")

# Test with invalid token
print("\n📋 Testing API with invalid token...")
bad_headers = {'Authorization': 'Bearer invalid_token', 'Content-Type': 'application/json'}
response = requests.get(f"{api_url}/timesheets", headers=bad_headers)
if response.status_code == 401:
    print("   ✅ Correctly rejected invalid token")
else:
    print(f"   ❌ Expected 401, got {response.status_code}")

print(f"\n{'='*60}")
print("✅ Edge case testing completed!")