#!/usr/bin/env python3
"""
Script zum Prüfen ob Dummy-Daten vorhanden sind
Verwendung: python check_dummy_data.py
"""

import asyncio
import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient

# Projekt-Pfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent))

# MongoDB-Verbindung
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "stundenzettel"

async def check_dummy_data():
    """Prüft ob Dummy-Daten vorhanden sind"""
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🔍 Prüfe Dummy-Daten in der Datenbank...\n")
    
    # Users prüfen
    user_count = await db.users.count_documents({})
    print(f"📝 Users: {user_count}")
    if user_count > 0:
        users = await db.users.find({}).to_list(length=10)
        for user in users:
            print(f"   - {user.get('name', 'Unbekannt')} ({user.get('email', 'keine Email')}) - {user.get('role', 'user')}")
    
    # Vehicles prüfen
    vehicle_count = await db.vehicles.count_documents({})
    print(f"\n🚗 Fahrzeuge: {vehicle_count}")
    if vehicle_count > 0:
        vehicles = await db.vehicles.find({}).to_list(length=10)
        for vehicle in vehicles:
            print(f"   - {vehicle.get('name', 'Unbekannt')} ({vehicle.get('license_plate', 'kein Kennzeichen')})")
    
    # Customers prüfen
    customer_count = await db.customers.count_documents({})
    print(f"\n👥 Kunden: {customer_count}")
    if customer_count > 0:
        customers = await db.customers.find({}).to_list(length=10)
        for customer in customers:
            print(f"   - {customer.get('name', 'Unbekannt')} ({'aktiv' if customer.get('active', False) else 'inaktiv'})")
    
    # Timesheets prüfen
    timesheet_count = await db.timesheets.count_documents({})
    print(f"\n📅 Stundenzettel: {timesheet_count}")
    if timesheet_count > 0:
        timesheets = await db.timesheets.find({}).to_list(length=10)
        for ts in timesheets:
            print(f"   - {ts.get('user_name', 'Unbekannt')} - {ts.get('week_start', 'kein Datum')} ({ts.get('status', 'unbekannt')})")
    
    # Travel Expenses prüfen
    expense_count = await db.travel_expenses.count_documents({})
    print(f"\n💼 Reisekosten-Einzelausgaben: {expense_count}")
    if expense_count > 0:
        expenses = await db.travel_expenses.find({}).to_list(length=10)
        for exp in expenses:
            print(f"   - {exp.get('user_name', 'Unbekannt')} - {exp.get('date', 'kein Datum')} - {exp.get('description', 'keine Beschreibung')} ({exp.get('status', 'unbekannt')})")
    
    # Travel Expense Reports prüfen
    report_count = await db.travel_expense_reports.count_documents({})
    print(f"\n📊 Reisekosten-Berichte: {report_count}")
    if report_count > 0:
        reports = await db.travel_expense_reports.find({}).to_list(length=10)
        for report in reports:
            print(f"   - {report.get('user_name', 'Unbekannt')} - {report.get('month', 'kein Monat')} ({report.get('status', 'unbekannt')})")
    
    # Vacation Requests prüfen
    vacation_count = await db.vacation_requests.count_documents({})
    print(f"\n🏖️  Urlaubsanträge: {vacation_count}")
    if vacation_count > 0:
        vacations = await db.vacation_requests.find({}).to_list(length=10)
        for vac in vacations:
            print(f"   - {vac.get('user_name', 'Unbekannt')} - {vac.get('start_date', 'kein Datum')} ({vac.get('status', 'unbekannt')})")
    
    # Vacation Balances prüfen
    balance_count = await db.vacation_balances.count_documents({})
    print(f"\n📅 Urlaubsguthaben: {balance_count}")
    if balance_count > 0:
        balances = await db.vacation_balances.find({}).to_list(length=10)
        for bal in balances:
            print(f"   - {bal.get('user_name', 'Unbekannt')} - {bal.get('year', 'kein Jahr')} ({bal.get('remaining_days', 0)} Tage)")
    
    # Announcements prüfen
    announcement_count = await db.announcements.count_documents({})
    print(f"\n📢 Ankündigungen: {announcement_count}")
    if announcement_count > 0:
        announcements = await db.announcements.find({}).to_list(length=10)
        for ann in announcements:
            print(f"   - {ann.get('title', 'Unbekannt')} ({'aktiv' if ann.get('active', False) else 'inaktiv'})")
    
    print("\n✅ Prüfung abgeschlossen!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_dummy_data())

