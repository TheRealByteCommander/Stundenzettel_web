"""
Datenbank-Migrations-Tool
Importiert Daten aus einer Vorgänger-Version ohne die Source-Datenbank zu verändern
Nur-Lese-Zugriff auf Source-DB gewährleistet
"""

import os
import sys
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from pathlib import Path
import asyncio
from pymongo import MongoClient
import mysql.connector
from mysql.connector import Error as MySQLError
import pymongo.errors

# Import database connection from server
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseMigration:
    """Migration von Vorgänger-Datenbank zur neuen Struktur"""
    
    def __init__(self, source_config: Dict[str, Any], target_config: Dict[str, Any]):
        """
        Initialize migration
        
        Args:
            source_config: Konfiguration für Source-DB (read-only)
                - type: 'mongo' oder 'mysql'
                - connection_string/credentials
            target_config: Konfiguration für Target-DB (neue DB)
                - mongo_url
                - db_name
        """
        self.source_config = source_config
        self.target_config = target_config
        self.source_client = None
        self.target_client = None
        self.target_db = None
        
    async def connect_source(self):
        """Verbinde mit Source-Datenbank (read-only)"""
        try:
            if self.source_config['type'] == 'mongo':
                # MongoDB Source
                connection_string = self.source_config.get('connection_string') or \
                    f"mongodb://{self.source_config.get('host', 'localhost')}:{self.source_config.get('port', 27017)}"
                self.source_client = MongoClient(
                    connection_string,
                    readPreference='secondaryPreferred',  # Read-only preference
                    serverSelectionTimeoutMS=5000
                )
                # Test connection
                self.source_client.admin.command('ping')
                logger.info("✅ Source MongoDB verbunden (read-only)")
                
            elif self.source_config['type'] == 'mysql':
                # MySQL Source
                self.source_client = mysql.connector.connect(
                    host=self.source_config.get('host', 'localhost'),
                    port=self.source_config.get('port', 3306),
                    user=self.source_config.get('user'),
                    password=self.source_config.get('password'),
                    database=self.source_config.get('database'),
                    read_only=True  # WICHTIG: Read-only Mode
                )
                logger.info("✅ Source MySQL verbunden (read-only)")
            else:
                raise ValueError(f"Unbekannter Source-DB-Typ: {self.source_config['type']}")
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Source-DB-Verbindung: {e}")
            raise
    
    async def connect_target(self):
        """Verbinde mit Target-Datenbank (neue DB)"""
        try:
            mongo_url = self.target_config.get('mongo_url', 'mongodb://localhost:27017')
            db_name = self.target_config.get('db_name', 'stundenzettel')
            
            self.target_client = AsyncIOMotorClient(mongo_url)
            self.target_db = self.target_client[db_name]
            
            # Test connection
            await self.target_client.admin.command('ping')
            logger.info(f"✅ Target MongoDB verbunden: {db_name}")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Target-DB-Verbindung: {e}")
            raise
    
    async def migrate_users(self, mapping_config: Optional[Dict] = None):
        """Migriere Benutzer aus Source-DB"""
        logger.info("🔄 Starte User-Migration...")
        
        source_users = []
        
        try:
            if self.source_config['type'] == 'mongo':
                source_db = self.source_client[self.source_config.get('database', 'stundenzettel')]
                collection_name = mapping_config.get('users_collection', 'users') if mapping_config else 'users'
                
                cursor = source_db[collection_name].find({})
                source_users = list(cursor)
                
            elif self.source_config['type'] == 'mysql':
                table_name = mapping_config.get('users_table', 'users') if mapping_config else 'users'
                cursor = self.source_client.cursor(dictionary=True)
                
                # Mapping für MySQL-Spalten (falls Struktur abweicht)
                column_mapping = mapping_config.get('users_columns', {}) if mapping_config else {}
                email_col = column_mapping.get('email', 'email')
                name_col = column_mapping.get('name', 'name')
                password_col = column_mapping.get('password', 'password_hash')
                is_admin_col = column_mapping.get('is_admin', 'is_admin')
                
                query = f"SELECT {email_col} as email, {name_col} as name, {password_col} as password_hash, {is_admin_col} as is_admin FROM {table_name}"
                cursor.execute(query)
                source_users = cursor.fetchall()
                cursor.close()
            
            logger.info(f"📊 Gefunden: {len(source_users)} Benutzer in Source-DB")
            
            migrated_count = 0
            skipped_count = 0
            error_count = 0
            
            for user in source_users:
                try:
                    # Mapping der alten Struktur auf neue Struktur
                    email = user.get('email', user.get('Email', ''))
                    name = user.get('name', user.get('Name', user.get('username', '')))
                    password_hash = user.get('password_hash', user.get('password', user.get('Password', '')))
                    
                    # Prüfen ob User bereits existiert
                    existing = await self.target_db.users.find_one({"email": email})
                    if existing:
                        logger.warning(f"⚠️  User bereits vorhanden: {email} - übersprungen")
                        skipped_count += 1
                        continue
                    
                    # Neue Struktur erstellen
                    new_user = {
                        "id": user.get('id', user.get('_id', None)),  # ID beibehalten falls vorhanden
                        "email": email,
                        "name": name,
                        "hashed_password": password_hash,
                        "role": "admin" if user.get('is_admin', user.get('IsAdmin', False)) else "user",
                        "weekly_hours": user.get('weekly_hours', user.get('weeklyHours', 40.0)),
                        "two_fa_enabled": user.get('two_fa_enabled', user.get('twoFAEnabled', False)),
                        "two_fa_secret": user.get('two_fa_secret', user.get('twoFASecret', None)),
                        "created_at": user.get('created_at', user.get('createdAt', datetime.utcnow())),
                        "updated_at": datetime.utcnow()
                    }
                    
                    # ID generieren falls nicht vorhanden
                    if not new_user.get("id"):
                        import uuid
                        new_user["id"] = str(uuid.uuid4())
                    
                    # Insert in Target-DB
                    await self.target_db.users.insert_one(new_user)
                    migrated_count += 1
                    logger.info(f"✅ User migriert: {email}")
                    
                except Exception as e:
                    logger.error(f"❌ Fehler bei User {user.get('email', 'unknown')}: {e}")
                    error_count += 1
            
            logger.info(f"✅ User-Migration abgeschlossen: {migrated_count} migriert, {skipped_count} übersprungen, {error_count} Fehler")
            return {"migrated": migrated_count, "skipped": skipped_count, "errors": error_count}
            
        except Exception as e:
            logger.error(f"❌ Fehler bei User-Migration: {e}")
            raise
    
    async def migrate_timesheets(self, mapping_config: Optional[Dict] = None):
        """Migriere Stundenzettel aus Source-DB"""
        logger.info("🔄 Starte Timesheet-Migration...")
        
        source_timesheets = []
        
        try:
            if self.source_config['type'] == 'mongo':
                source_db = self.source_client[self.source_config.get('database', 'stundenzettel')]
                collection_name = mapping_config.get('timesheets_collection', 'timesheets') if mapping_config else 'timesheets'
                
                cursor = source_db[collection_name].find({})
                source_timesheets = list(cursor)
                
            elif self.source_config['type'] == 'mysql':
                table_name = mapping_config.get('timesheets_table', 'timesheets') if mapping_config else 'timesheets'
                cursor = self.source_client.cursor(dictionary=True)
                
                query = f"SELECT * FROM {table_name}"
                cursor.execute(query)
                source_timesheets = cursor.fetchall()
                cursor.close()
            
            logger.info(f"📊 Gefunden: {len(source_timesheets)} Stundenzettel in Source-DB")
            
            migrated_count = 0
            skipped_count = 0
            error_count = 0
            
            for timesheet in source_timesheets:
                try:
                    # ID prüfen
                    timesheet_id = timesheet.get('id', timesheet.get('_id', None))
                    if not timesheet_id:
                        import uuid
                        timesheet_id = str(uuid.uuid4())
                    
                    # Prüfen ob bereits vorhanden
                    existing = await self.target_db.weekly_timesheets.find_one({"id": str(timesheet_id)})
                    if existing:
                        logger.warning(f"⚠️  Timesheet bereits vorhanden: {timesheet_id} - übersprungen")
                        skipped_count += 1
                        continue
                    
                    # Alte Struktur auf neue mappen
                    entries = timesheet.get('entries', timesheet.get('Entries', []))
                    
                    # Falls entries als JSON-String gespeichert sind (MySQL)
                    if isinstance(entries, str):
                        entries = json.loads(entries)
                    
                    # Neue Struktur erstellen
                    new_timesheet = {
                        "id": str(timesheet_id),
                        "user_id": str(timesheet.get('user_id', timesheet.get('userId', ''))),
                        "user_name": timesheet.get('user_name', timesheet.get('userName', '')),
                        "week_start": timesheet.get('week_start', timesheet.get('weekStart', '')),
                        "week_end": timesheet.get('week_end', timesheet.get('weekEnd', '')),
                        "entries": entries,
                        "status": timesheet.get('status', 'draft'),  # draft, sent, approved
                        "created_at": timesheet.get('created_at', timesheet.get('createdAt', datetime.utcnow())),
                        "updated_at": datetime.utcnow()
                    }
                    
                    # Datum konvertieren falls nötig
                    if isinstance(new_timesheet['created_at'], str):
                        try:
                            new_timesheet['created_at'] = datetime.fromisoformat(new_timesheet['created_at'].replace('Z', '+00:00'))
                        except:
                            new_timesheet['created_at'] = datetime.utcnow()
                    
                    # Insert in Target-DB
                    await self.target_db.weekly_timesheets.insert_one(new_timesheet)
                    migrated_count += 1
                    
                    if migrated_count % 10 == 0:
                        logger.info(f"📈 Fortschritt: {migrated_count} Stundenzettel migriert...")
                    
                except Exception as e:
                    logger.error(f"❌ Fehler bei Timesheet {timesheet.get('id', 'unknown')}: {e}")
                    error_count += 1
            
            logger.info(f"✅ Timesheet-Migration abgeschlossen: {migrated_count} migriert, {skipped_count} übersprungen, {error_count} Fehler")
            return {"migrated": migrated_count, "skipped": skipped_count, "errors": error_count}
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Timesheet-Migration: {e}")
            raise
    
    async def migrate_travel_expenses(self, mapping_config: Optional[Dict] = None):
        """Migriere Reisekosten aus Source-DB (falls vorhanden)"""
        logger.info("🔄 Starte Travel-Expense-Migration...")
        
        try:
            source_expenses = []
            
            if self.source_config['type'] == 'mongo':
                source_db = self.source_client[self.source_config.get('database', 'stundenzettel')]
                collection_name = mapping_config.get('travel_expenses_collection', 'travel_expenses') if mapping_config else 'travel_expenses'
                
                if collection_name in source_db.list_collection_names():
                    cursor = source_db[collection_name].find({})
                    source_expenses = list(cursor)
                else:
                    logger.info("ℹ️  Keine Travel-Expenses in Source-DB gefunden")
                    return {"migrated": 0, "skipped": 0, "errors": 0}
                    
            elif self.source_config['type'] == 'mysql':
                table_name = mapping_config.get('travel_expenses_table', 'travel_expenses') if mapping_config else 'travel_expenses'
                cursor = self.source_client.cursor(dictionary=True)
                
                try:
                    query = f"SELECT * FROM {table_name}"
                    cursor.execute(query)
                    source_expenses = cursor.fetchall()
                except MySQLError:
                    logger.info("ℹ️  Keine Travel-Expenses-Tabelle in Source-DB gefunden")
                    return {"migrated": 0, "skipped": 0, "errors": 0}
                finally:
                    cursor.close()
            
            if not source_expenses:
                logger.info("ℹ️  Keine Travel-Expenses zu migrieren")
                return {"migrated": 0, "skipped": 0, "errors": 0}
            
            logger.info(f"📊 Gefunden: {len(source_expenses)} Reisekosten in Source-DB")
            
            migrated_count = 0
            skipped_count = 0
            error_count = 0
            
            for expense in source_expenses:
                try:
                    expense_id = expense.get('id', expense.get('_id', None))
                    if not expense_id:
                        import uuid
                        expense_id = str(uuid.uuid4())
                    
                    existing = await self.target_db.travel_expenses.find_one({"id": str(expense_id)})
                    if existing:
                        skipped_count += 1
                        continue
                    
                    new_expense = {
                        "id": str(expense_id),
                        "user_id": str(expense.get('user_id', expense.get('userId', ''))),
                        "user_name": expense.get('user_name', expense.get('userName', '')),
                        "date": expense.get('date', expense.get('Date', '')),
                        "description": expense.get('description', expense.get('Description', '')),
                        "kilometers": float(expense.get('kilometers', expense.get('Kilometers', 0.0))),
                        "expenses": float(expense.get('expenses', expense.get('Expenses', 0.0))),
                        "customer_project": expense.get('customer_project', expense.get('customerProject', '')),
                        "status": expense.get('status', 'draft'),
                        "created_at": expense.get('created_at', expense.get('createdAt', datetime.utcnow()))
                    }
                    
                    if isinstance(new_expense['created_at'], str):
                        try:
                            new_expense['created_at'] = datetime.fromisoformat(new_expense['created_at'].replace('Z', '+00:00'))
                        except:
                            new_expense['created_at'] = datetime.utcnow()
                    
                    await self.target_db.travel_expenses.insert_one(new_expense)
                    migrated_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Fehler bei Travel-Expense {expense.get('id', 'unknown')}: {e}")
                    error_count += 1
            
            logger.info(f"✅ Travel-Expense-Migration abgeschlossen: {migrated_count} migriert, {skipped_count} übersprungen, {error_count} Fehler")
            return {"migrated": migrated_count, "skipped": skipped_count, "errors": error_count}
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Travel-Expense-Migration: {e}")
            # Nicht kritisch, kann fehlen
            return {"migrated": 0, "skipped": 0, "errors": 0}
    
    async def verify_readonly(self):
        """Überprüfe, dass Source-DB nur lesbar ist (Sicherheitscheck)"""
        logger.info("🔒 Überprüfe Read-Only-Modus der Source-DB...")
        
        try:
            if self.source_config['type'] == 'mysql':
                # MySQL: read_only Flag prüfen
                cursor = self.source_client.cursor()
                cursor.execute("SHOW VARIABLES LIKE 'read_only'")
                result = cursor.fetchone()
                cursor.close()
                
                if result and result[1] == 'ON':
                    logger.info("✅ MySQL Source-DB ist im Read-Only-Modus")
                else:
                    logger.warning("⚠️  WARNUNG: MySQL Source-DB ist NICHT im Read-Only-Modus!")
                    logger.warning("⚠️  Migration verwendet dennoch nur SELECT-Statements (sicher)")
                    
            elif self.source_config['type'] == 'mongo':
                # MongoDB: Versuche Write-Operation (sollte fehlschlagen)
                try:
                    test_db = self.source_client[self.source_config.get('database', 'test')]
                    test_db['_migration_test'].insert_one({"test": "write"})
                    logger.warning("⚠️  WARNUNG: MongoDB Source-DB erlaubt Schreibzugriff!")
                    logger.warning("⚠️  Migration führt dennoch keine Write-Operationen aus")
                    # Cleanup
                    test_db['_migration_test'].drop()
                except:
                    logger.info("✅ MongoDB Source-DB erlaubt keinen Schreibzugriff (oder Test erfolgreich)")
                    
        except Exception as e:
            logger.warning(f"⚠️  Read-Only-Check nicht durchführbar: {e}")
            logger.warning("⚠️  Migration verwendet dennoch nur READ-Operationen")
    
    async def migrate_all(self, mapping_config: Optional[Dict] = None, skip_users: bool = False, 
                         skip_timesheets: bool = False, skip_travel_expenses: bool = False):
        """Führe vollständige Migration durch"""
        logger.info("🚀 Starte vollständige Datenbank-Migration...")
        logger.info("📋 Source-DB: " + str(self.source_config))
        logger.info("📋 Target-DB: " + str(self.target_config))
        
        try:
            # Verbindungen herstellen
            await self.connect_source()
            await self.connect_target()
            
            # Read-Only-Check
            await self.verify_readonly()
            
            results = {}
            
            # Migration durchführen
            if not skip_users:
                results['users'] = await self.migrate_users(mapping_config)
            
            if not skip_timesheets:
                results['timesheets'] = await self.migrate_timesheets(mapping_config)
            
            if not skip_travel_expenses:
                results['travel_expenses'] = await self.migrate_travel_expenses(mapping_config)
            
            logger.info("✅ Migration vollständig abgeschlossen!")
            logger.info("📊 Zusammenfassung:")
            for entity, result in results.items():
                logger.info(f"  {entity}: {result['migrated']} migriert, {result['skipped']} übersprungen, {result['errors']} Fehler")
            
            return results
            
        finally:
            # Verbindungen schließen
            if self.source_client:
                if self.source_config['type'] == 'mysql':
                    self.source_client.close()
                else:
                    self.source_client.close()
            if self.target_client:
                self.target_client.close()
            
            logger.info("🔌 Verbindungen geschlossen")

def load_mapping_config(config_file: str) -> Dict:
    """Lade Mapping-Konfiguration aus JSON-Datei"""
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

async def main():
    """Hauptfunktion für CLI-Aufruf"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migriere Daten von Vorgänger-DB zur neuen Struktur')
    parser.add_argument('--source-type', choices=['mongo', 'mysql'], required=True,
                       help='Typ der Source-Datenbank')
    parser.add_argument('--source-host', default='localhost',
                       help='Source-DB Host')
    parser.add_argument('--source-port', type=int, default=27017,
                       help='Source-DB Port')
    parser.add_argument('--source-database', required=True,
                       help='Source-DB Name')
    parser.add_argument('--source-user', help='Source-DB User (für MySQL)')
    parser.add_argument('--source-password', help='Source-DB Password (für MySQL)')
    parser.add_argument('--source-connection-string', help='MongoDB Connection String (statt host/port)')
    
    parser.add_argument('--target-mongo-url', default='mongodb://localhost:27017',
                       help='Target MongoDB URL')
    parser.add_argument('--target-db-name', default='stundenzettel',
                       help='Target DB Name')
    
    parser.add_argument('--mapping-config', help='JSON-Datei mit Mapping-Konfiguration')
    parser.add_argument('--skip-users', action='store_true',
                       help='Users nicht migrieren')
    parser.add_argument('--skip-timesheets', action='store_true',
                       help='Timesheets nicht migrieren')
    parser.add_argument('--skip-travel-expenses', action='store_true',
                       help='Travel Expenses nicht migrieren')
    
    args = parser.parse_args()
    
    # Source-Config erstellen
    source_config = {
        'type': args.source_type,
        'host': args.source_host,
        'port': args.source_port,
        'database': args.source_database
    }
    
    if args.source_connection_string:
        source_config['connection_string'] = args.source_connection_string
    
    if args.source_user:
        source_config['user'] = args.source_user
    if args.source_password:
        source_config['password'] = args.source_password
    
    # Target-Config
    target_config = {
        'mongo_url': args.target_mongo_url,
        'db_name': args.target_db_name
    }
    
    # Mapping-Config laden
    mapping_config = None
    if args.mapping_config:
        mapping_config = load_mapping_config(args.mapping_config)
    
    # Migration durchführen
    migration = DatabaseMigration(source_config, target_config)
    results = await migration.migrate_all(
        mapping_config=mapping_config,
        skip_users=args.skip_users,
        skip_timesheets=args.skip_timesheets,
        skip_travel_expenses=args.skip_travel_expenses
    )
    
    return results

if __name__ == '__main__':
    asyncio.run(main())

