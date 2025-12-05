#!/usr/bin/env python3
"""
Script zum Erstellen von Dummy-Daten für alle Entitäten
Verwendung: python create_dummy_data.py
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
import uuid

# MongoDB Client
from motor.motor_asyncio import AsyncIOMotorClient

# Password hashing - verwende die gleiche Methode wie im Backend
import os
os.environ.setdefault("PASSLIB_DISABLED_HASHES", "bcrypt")
from passlib.context import CryptContext
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)

# Projekt-Pfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent))

# MongoDB-Verbindung
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "stundenzettel"

async def create_dummy_data():
    """Erstellt Dummy-Daten für alle Entitäten"""
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🚀 Starte Erstellung von Dummy-Daten...")
    
    # 1. Users erstellen
    print("\n📝 Erstelle Users...")
    
    # Passwort-Hashes generieren (alle Passwörter: "test123")
    default_password_hash = pwd_context.hash("test123")
    
    users = [
        {
            "id": "user-admin-001",
            "email": "admin@tick-guard.de",
            "name": "Max Mustermann",
            "role": "admin",
            "hashed_password": default_password_hash,
            "created_at": datetime.utcnow(),
        },
        {
            "id": "user-accounting-001",
            "email": "buchhaltung@tick-guard.de",
            "name": "Anna Schmidt",
            "role": "accounting",
            "hashed_password": default_password_hash,
            "created_at": datetime.utcnow(),
        },
        {
            "id": "user-001",
            "email": "mitarbeiter1@tick-guard.de",
            "name": "Peter Müller",
            "role": "user",
            "hashed_password": default_password_hash,
            "created_at": datetime.utcnow(),
        },
        {
            "id": "user-002",
            "email": "mitarbeiter2@tick-guard.de",
            "name": "Lisa Weber",
            "role": "user",
            "hashed_password": default_password_hash,
            "created_at": datetime.utcnow(),
        },
        {
            "id": "user-003",
            "email": "mitarbeiter3@tick-guard.de",
            "name": "Thomas Fischer",
            "role": "user",
            "hashed_password": default_password_hash,
            "created_at": datetime.utcnow(),
        },
    ]
    
    for user in users:
        existing = await db.users.find_one({"email": user["email"]})
        if not existing:
            await db.users.insert_one(user)
            print(f"  ✅ User erstellt: {user['name']} ({user['email']})")
        else:
            print(f"  ⏭️  User existiert bereits: {user['email']}")
    
    # 2. Vehicles erstellen
    print("\n🚗 Erstelle Fahrzeuge...")
    vehicles = [
        {
            "id": "vehicle-001",
            "name": "Firmenwagen 1",
            "license_plate": "B-AB 1234",
            "is_pool": True,
            "assigned_user_id": None,
            "assigned_user_name": None,
            "created_at": datetime.utcnow(),
        },
        {
            "id": "vehicle-002",
            "name": "Firmenwagen 2",
            "license_plate": "B-CD 5678",
            "is_pool": True,
            "assigned_user_id": None,
            "assigned_user_name": None,
            "created_at": datetime.utcnow(),
        },
        {
            "id": "vehicle-003",
            "name": "Privatfahrzeug Peter",
            "license_plate": "B-EF 9012",
            "is_pool": False,
            "assigned_user_id": "user-001",
            "assigned_user_name": "Peter Müller",
            "created_at": datetime.utcnow(),
        },
    ]
    
    for vehicle in vehicles:
        existing = await db.vehicles.find_one({"id": vehicle["id"]})
        if not existing:
            await db.vehicles.insert_one(vehicle)
            print(f"  ✅ Fahrzeug erstellt: {vehicle['name']} ({vehicle['license_plate']})")
        else:
            print(f"  ⏭️  Fahrzeug existiert bereits: {vehicle['license_plate']}")
    
    # 3. Customers erstellen
    print("\n👥 Erstelle Kunden...")
    customers = [
        {
            "id": "customer-001",
            "name": "ACME GmbH",
            "project_name": "Projekt Alpha",
            "contact_person": "Herr Schmidt",
            "email": "schmidt@acme.de",
            "phone": "+49 30 12345678",
            "address": "Musterstraße 1, 10115 Berlin",
            "active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "id": "customer-002",
            "name": "Tech Solutions AG",
            "project_name": "Digitalisierung",
            "contact_person": "Frau Müller",
            "email": "mueller@tech-solutions.de",
            "phone": "+49 30 87654321",
            "address": "Hauptstraße 42, 20095 Hamburg",
            "active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "id": "customer-003",
            "name": "Startup Innovations",
            "project_name": None,
            "contact_person": "Herr Weber",
            "email": "weber@startup.de",
            "phone": "+49 30 11223344",
            "address": "Innovationsweg 5, 80331 München",
            "active": True,
            "created_at": datetime.utcnow(),
        },
    ]
    
    for customer in customers:
        existing = await db.customers.find_one({"id": customer["id"]})
        if not existing:
            await db.customers.insert_one(customer)
            print(f"  ✅ Kunde erstellt: {customer['name']}")
        else:
            print(f"  ⏭️  Kunde existiert bereits: {customer['name']}")
    
    # 4. Timesheets erstellen
    print("\n📅 Erstelle Stundenzettel...")
    
    # Berechne Montag der aktuellen Woche
    today = datetime.now()
    days_since_monday = today.weekday()
    monday = today - timedelta(days=days_since_monday)
    week_start = monday.strftime("%Y-%m-%d")
    week_end = (monday + timedelta(days=6)).strftime("%Y-%m-%d")
    
    timesheets = []
    for i, user_id in enumerate(["user-001", "user-002", "user-003"]):
        user_name = users[i + 2]["name"]  # user-001, user-002, user-003
        week_date = monday - timedelta(weeks=i)
        
        entries = []
        for day in range(5):  # Montag bis Freitag
            entry_date = week_date + timedelta(days=day)
            entries.append({
                "date": entry_date.strftime("%Y-%m-%d"),
                "start_time": "08:00",
                "end_time": "17:00",
                "break_minutes": 30,
                "tasks": f"Projektarbeit Tag {day + 1}",
                "location": "Büro",
                "customer_project": customers[i % len(customers)]["name"] if i < len(customers) else customers[0]["name"],
                "vehicle_id": "vehicle-001" if i == 0 else None,
            })
        
        timesheet = {
            "id": f"timesheet-{user_id}-{week_date.strftime('%Y%m%d')}",
            "user_id": user_id,
            "user_name": user_name,
            "week_start": week_date.strftime("%Y-%m-%d"),
            "week_end": (week_date + timedelta(days=6)).strftime("%Y-%m-%d"),
            "entries": entries,
            "status": "draft" if i == 0 else "approved" if i == 1 else "sent",
            "week_vehicle_id": "vehicle-001" if i == 0 else None,
            "created_at": datetime.utcnow(),
        }
        timesheets.append(timesheet)
    
    for timesheet in timesheets:
        existing = await db.timesheets.find_one({"id": timesheet["id"]})
        if not existing:
            await db.timesheets.insert_one(timesheet)
            print(f"  ✅ Stundenzettel erstellt: {timesheet['user_name']} - {timesheet['week_start']} ({timesheet['status']})")
        else:
            print(f"  ⏭️  Stundenzettel existiert bereits: {timesheet['id']}")
    
    # 5. Travel Expenses (Einzelausgaben) erstellen
    print("\n💼 Erstelle Reisekosten-Einzelausgaben...")
    
    travel_expenses = []
    for i, user_id in enumerate(["user-001", "user-002"]):
        user_name = users[i + 2]["name"]
        expense_date = (datetime.now() - timedelta(days=i * 2)).strftime("%Y-%m-%d")
        
        expense = {
            "id": f"expense-{user_id}-{i + 1}",
            "user_id": user_id,
            "user_name": user_name,
            "date": expense_date,
            "description": f"Hotelübernachtung Berlin" if i == 0 else "Bahnfahrt nach Hamburg",
            "kilometers": 0.0,
            "expenses": 0.0,
            "customer_project": customers[i % len(customers)]["name"],
            "receipts": [],
            "status": "draft",
            "created_at": datetime.utcnow(),
        }
        travel_expenses.append(expense)
    
    for expense in travel_expenses:
        existing = await db.travel_expenses.find_one({"id": expense["id"]})
        if not existing:
            await db.travel_expenses.insert_one(expense)
            print(f"  ✅ Reisekosten erstellt: {expense['user_name']} - {expense['description']}")
        else:
            print(f"  ⏭️  Reisekosten existiert bereits: {expense['id']}")
    
    # 6. Travel Expense Reports erstellen
    print("\n📊 Erstelle Reisekosten-Berichte...")
    
    current_month = datetime.now().strftime("%Y-%m")
    report = {
        "id": f"report-{current_month}",
        "user_id": "user-001",
        "user_name": "Peter Müller",
        "month": current_month,
        "entries": [
            {
                "date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
                "location": "Berlin",
                "customer_project": customers[0]["name"],
                "kilometers": 150.0,
                "hours": 2.5,
            },
            {
                "date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
                "location": "Hamburg",
                "customer_project": customers[1]["name"],
                "kilometers": 200.0,
                "hours": 3.0,
            },
        ],
        "status": "draft",
        "receipts": [],
        "created_at": datetime.utcnow(),
    }
    
    existing = await db.travel_expense_reports.find_one({"id": report["id"]})
    if not existing:
        await db.travel_expense_reports.insert_one(report)
        print(f"  ✅ Reisekosten-Bericht erstellt: {report['month']}")
    else:
        print(f"  ⏭️  Reisekosten-Bericht existiert bereits: {report['month']}")
    
    # 7. Vacation Requests erstellen
    print("\n🏖️  Erstelle Urlaubsanträge...")
    
    vacation_requests = [
        {
            "id": "vacation-001",
            "user_id": "user-001",
            "user_name": "Peter Müller",
            "start_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=37)).strftime("%Y-%m-%d"),
            "days": 6,
            "status": "pending",
            "created_at": datetime.utcnow(),
        },
        {
            "id": "vacation-002",
            "user_id": "user-002",
            "user_name": "Lisa Weber",
            "start_date": (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=67)).strftime("%Y-%m-%d"),
            "days": 6,
            "status": "approved",
            "reviewed_at": datetime.utcnow(),
            "reviewed_by": "user-admin-001",
            "created_at": datetime.utcnow() - timedelta(days=10),
        },
    ]
    
    for request in vacation_requests:
        existing = await db.vacation_requests.find_one({"id": request["id"]})
        if not existing:
            await db.vacation_requests.insert_one(request)
            print(f"  ✅ Urlaubsantrag erstellt: {request['user_name']} - {request['start_date']} ({request['status']})")
        else:
            print(f"  ⏭️  Urlaubsantrag existiert bereits: {request['id']}")
    
    # 8. Vacation Balances erstellen
    print("\n📅 Erstelle Urlaubsguthaben...")
    
    current_year = datetime.now().year
    vacation_balances = [
        {
            "id": f"balance-user-001-{current_year}",
            "user_id": "user-001",
            "user_name": "Peter Müller",
            "year": current_year,
            "total_days": 25,
            "used_days": 5,
            "remaining_days": 20,
            "created_at": datetime.utcnow(),
        },
        {
            "id": f"balance-user-002-{current_year}",
            "user_id": "user-002",
            "user_name": "Lisa Weber",
            "year": current_year,
            "total_days": 30,
            "used_days": 10,
            "remaining_days": 20,
            "created_at": datetime.utcnow(),
        },
        {
            "id": f"balance-user-003-{current_year}",
            "user_id": "user-003",
            "user_name": "Thomas Fischer",
            "year": current_year,
            "total_days": 28,
            "used_days": 0,
            "remaining_days": 28,
            "created_at": datetime.utcnow(),
        },
    ]
    
    for balance in vacation_balances:
        existing = await db.vacation_balances.find_one({"id": balance["id"]})
        if not existing:
            await db.vacation_balances.insert_one(balance)
            print(f"  ✅ Urlaubsguthaben erstellt: {balance['user_name']} - {balance['year']} ({balance['remaining_days']} Tage)")
        else:
            print(f"  ⏭️  Urlaubsguthaben existiert bereits: {balance['id']}")
    
    # 9. Announcements erstellen
    print("\n📢 Erstelle Ankündigungen...")
    
    announcements = [
        {
            "id": "announcement-001",
            "title": "Willkommen bei Tick Guard",
            "content": "<p>Willkommen im neuen Tick Guard System! Bitte nehmen Sie sich Zeit, um sich mit den Funktionen vertraut zu machen.</p>",
            "active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "id": "announcement-002",
            "title": "Wichtiger Hinweis: Stundenzettel",
            "content": "<p>Bitte denken Sie daran, Ihre Stundenzettel wöchentlich einzureichen. Vielen Dank!</p>",
            "active": True,
            "created_at": datetime.utcnow() - timedelta(days=5),
        },
        {
            "id": "announcement-003",
            "title": "Alte Ankündigung",
            "content": "<p>Diese Ankündigung ist inaktiv.</p>",
            "active": False,
            "created_at": datetime.utcnow() - timedelta(days=30),
        },
    ]
    
    for announcement in announcements:
        existing = await db.announcements.find_one({"id": announcement["id"]})
        if not existing:
            await db.announcements.insert_one(announcement)
            print(f"  ✅ Ankündigung erstellt: {announcement['title']} ({'aktiv' if announcement['active'] else 'inaktiv'})")
        else:
            print(f"  ⏭️  Ankündigung existiert bereits: {announcement['id']}")
    
    # 10. Notification Preferences erstellen
    print("\n🔔 Erstelle Benachrichtigungseinstellungen...")
    
    for user_id in ["user-001", "user-002", "user-003"]:
        prefs = {
            "user_id": user_id,
            "email_notifications": {
                "timesheet_reminder": True,
                "vacation_request": True,
                "expense_approved": True,
                "admin_announcement": True,
            },
            "push_notifications": {
                "timesheet_reminder": False,
                "vacation_request": True,
                "expense_approved": True,
                "admin_announcement": True,
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        existing = await db.notification_preferences.find_one({"user_id": user_id})
        if not existing:
            await db.notification_preferences.insert_one(prefs)
            print(f"  ✅ Benachrichtigungseinstellungen erstellt: {user_id}")
        else:
            print(f"  ⏭️  Benachrichtigungseinstellungen existieren bereits: {user_id}")
    
    print("\n✅ Dummy-Daten erfolgreich erstellt!")
    print("\n📋 Zusammenfassung:")
    print(f"  - {len(users)} Users")
    print(f"  - {len(vehicles)} Fahrzeuge")
    print(f"  - {len(customers)} Kunden")
    print(f"  - {len(timesheets)} Stundenzettel")
    print(f"  - {len(travel_expenses)} Reisekosten-Einzelausgaben")
    print(f"  - 1 Reisekosten-Bericht")
    print(f"  - {len(vacation_requests)} Urlaubsanträge")
    print(f"  - {len(vacation_balances)} Urlaubsguthaben")
    print(f"  - {len(announcements)} Ankündigungen")
    print(f"  - 3 Benachrichtigungseinstellungen")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_dummy_data())

