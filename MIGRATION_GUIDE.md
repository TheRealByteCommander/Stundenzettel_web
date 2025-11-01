# 🔄 Datenbank-Migrations-Guide

## Übersicht

Dieses Tool ermöglicht die sichere Migration von Daten aus einer Vorgänger-Version der Zeiterfassungs-Software in die neue Datenbankstruktur.

**🔒 Sicherheit:** Die Source-Datenbank wird **NIE verändert** - nur gelesen!

---

## 🎯 Was wird migriert?

- ✅ **Benutzer (Users)**: Email, Name, Passwort, Admin-Rechte, Wochenstunden
- ✅ **Stundenzettel (Timesheets)**: Alle Wochenstundenzettel mit Einträgen
- ✅ **Reisekosten (Travel Expenses)**: Falls in alter DB vorhanden

---

## 📋 Voraussetzungen

### Source-Datenbank

Die Migration unterstützt:
- **MongoDB** (alte Version)
- **MySQL** (alte Version)

### Target-Datenbank

- **MongoDB** (neue Struktur)
- Muss bereits existieren oder wird beim ersten Start erstellt

### Python-Abhängigkeiten

```bash
cd backend
pip install mysql-connector-python
```

---

## 🚀 Schnellstart

### 1. Source-Datenbank vorbereiten (Read-Only)

**MySQL:**
```sql
-- Als Datenbank-Admin
SET GLOBAL read_only = ON;
SET GLOBAL super_read_only = ON;
```

**MongoDB:**
- Erstellen Sie einen Read-Only User:
```javascript
use admin
db.createUser({
  user: "migration_reader",
  pwd: "SicheresPasswort",
  roles: [{ role: "read", db: "alte_db_name" }]
})
```

### 2. Migration durchführen

#### Option A: Kommandozeile (Empfohlen)

**Von MongoDB:**
```bash
cd backend
python migration_tool.py \
  --source-type mongo \
  --source-host localhost \
  --source-port 27017 \
  --source-database alte_stundenzettel_db \
  --target-mongo-url mongodb://localhost:27017 \
  --target-db-name stundenzettel
```

**Von MySQL:**
```bash
python migration_tool.py \
  --source-type mysql \
  --source-host localhost \
  --source-port 3306 \
  --source-database alte_stundenzettel_db \
  --source-user db_reader \
  --source-password sicheres_passwort \
  --target-mongo-url mongodb://localhost:27017 \
  --target-db-name stundenzettel
```

#### Option B: Mit Mapping-Konfiguration

1. Erstellen Sie `migration_config.json`:
```json
{
  "mappings": {
    "users": {
      "collection": "benutzer",
      "field_mappings": {
        "email": "Email",
        "name": "VollständigerName",
        "password_hash": "PasswortHash",
        "is_admin": "IstAdministrator"
      }
    }
  },
  "mysql_mappings": {
    "users": {
      "table": "users",
      "columns": {
        "email": "email_spalte",
        "name": "name_spalte"
      }
    }
  }
}
```

2. Migration ausführen:
```bash
python migration_tool.py \
  --source-type mysql \
  --source-database alte_db \
  --target-db-name stundenzettel \
  --mapping-config migration_config.json
```

---

## 📊 Schritt-für-Schritt Anleitung

### Schritt 1: Source-DB analysieren

**MongoDB:**
```javascript
// In MongoDB Shell
use alte_db_name
show collections
db.users.find().limit(1)
db.timesheets.find().limit(1)
```

**MySQL:**
```sql
-- In MySQL
USE alte_db_name;
SHOW TABLES;
SELECT * FROM users LIMIT 1;
SELECT * FROM timesheets LIMIT 1;
```

Notieren Sie sich:
- Collection-/Tabellennamen
- Feldnamen
- Datentypen

### Schritt 2: Backup erstellen

**Target-DB Backup:**
```bash
mongodump --uri="mongodb://localhost:27017/stundenzettel" --out=/backup/pre_migration_$(date +%Y%m%d)
```

### Schritt 3: Mapping-Konfiguration erstellen

Erstellen Sie `migration_config.json` basierend auf Ihrer Source-DB-Struktur.

Siehe `migration_config_example.json` für Beispiel.

### Schritt 4: Test-Migration

```bash
python migration_tool.py \
  --source-type mysql \
  --source-database alte_db \
  --target-db-name stundenzettel_test \
  --mapping-config migration_config.json \
  --skip-travel-expenses
```

### Schritt 5: Daten prüfen

```bash
mongosh
use stundenzettel_test
db.users.countDocuments({})
db.weekly_timesheets.countDocuments({})
db.users.findOne()
```

### Schritt 6: Vollständige Migration

Nach erfolgreicher Test-Migration:

```bash
python migration_tool.py \
  --source-type mysql \
  --source-database alte_db \
  --target-db-name stundenzettel \
  --mapping-config migration_config.json
```

---

## ⚙️ Erweiterte Optionen

### Nur bestimmte Daten migrieren

```bash
# Nur Users
python migration_tool.py \
  --source-type mysql \
  --source-database alte_db \
  --skip-timesheets \
  --skip-travel-expenses

# Nur Timesheets
python migration_tool.py \
  --source-type mysql \
  --source-database alte_db \
  --skip-users \
  --skip-travel-expenses
```

### Inkrementelle Migration

Das Tool kann mehrfach ausgeführt werden - bereits migrierte Daten werden automatisch übersprungen:

```bash
# Erste Migration
python migration_tool.py --source-type mysql --source-database alte_db

# Später: Neue Daten hinzufügen (nur neue werden migriert)
python migration_tool.py --source-type mysql --source-database alte_db
```

---

## 🔍 Validierung nach Migration

### Datenanzahl prüfen

```python
from motor.motor_asyncio import AsyncIOMotorClient

async def validate():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['stundenzettel']
    
    users = await db.users.count_documents({})
    timesheets = await db.weekly_timesheets.count_documents({})
    
    print(f"Users: {users}")
    print(f"Timesheets: {timesheets}")

import asyncio
asyncio.run(validate())
```

### Stichproben prüfen

```javascript
// In MongoDB Shell
use stundenzettel

// Zufällige User prüfen
db.users.aggregate([{ $sample: { size: 5 } }])

// Stundenzettel mit Einträgen prüfen
db.weekly_timesheets.find({ "entries": { $exists: true, $ne: [] } }).limit(5)

// Admin-User prüfen
db.users.find({ "role": "admin" })
```

---

## 🐛 Häufige Probleme

### Problem: "Collection not found"

**Lösung:**
- Überprüfen Sie Collection-/Tabellennamen in Source-DB
- Passen Sie Mapping-Konfiguration an
- Verwenden Sie `--mapping-config`

### Problem: "Field not found"

**Lösung:**
- Analysieren Sie die Source-DB-Struktur
- Aktualisieren Sie `field_mappings` in `migration_config.json`

### Problem: "Connection refused"

**Lösung:**
- Überprüfen Sie Host/Port
- Prüfen Sie Firewall-Einstellungen
- Für MySQL: Prüfen Sie remote-Zugriff

### Problem: "Duplicate key error"

**Lösung:**
- Normal - bereits vorhandene Daten werden übersprungen
- Prüfen Sie Logs für Details

---

## 📝 Beispiel: Migration von alter MySQL-DB

**1. Source-DB analysieren:**

```sql
USE alte_stundenzettel;
SHOW TABLES;
-- Ergebnis: users, timesheets, settings

DESCRIBE users;
-- email, name, password, admin_flag
```

**2. Mapping-Konfiguration erstellen:**

```json
{
  "mysql_mappings": {
    "users": {
      "table": "users",
      "columns": {
        "email": "email",
        "name": "name",
        "password": "password",
        "is_admin": "admin_flag"
      }
    },
    "timesheets": {
      "table": "timesheets",
      "columns": {
        "id": "id",
        "user_id": "user_id",
        "week_start": "week_start",
        "week_end": "week_end",
        "entries": "entries_json"
      }
    }
  }
}
```

**3. Migration ausführen:**

```bash
python migration_tool.py \
  --source-type mysql \
  --source-host localhost \
  --source-port 3306 \
  --source-database alte_stundenzettel \
  --source-user migration_reader \
  --source-password sicheres_passwort \
  --target-mongo-url mongodb://localhost:27017 \
  --target-db-name stundenzettel \
  --mapping-config migration_config.json
```

---

## 🔐 Sicherheit: Best Practices

1. **Source-DB Read-Only setzen:**
   - MySQL: `SET GLOBAL read_only = ON`
   - MongoDB: Read-Only User erstellen

2. **Backup vor Migration:**
   ```bash
   mongodump --uri="mongodb://localhost:27017/stundenzettel" --out=/backup/pre_migration
   ```

3. **Test-Migration zuerst:**
   - Verwenden Sie Test-Datenbank
   - Prüfen Sie Ergebnisse
   - Dann vollständige Migration

4. **Logs überprüfen:**
   - Migration-Logs prüfen
   - Fehler analysieren
   - Erfolgreich migrierte Daten zählen

5. **Nach Migration:**
   - Daten in neuer DB validieren
   - Test-Login durchführen
   - Funktionen testen

---

## 📞 Support

Bei Fragen oder Problemen:
- Prüfen Sie die Logs
- Siehe `MIGRATION_README.md` für Details
- Kontaktieren Sie den Support

---

**Migration erfolgreich abgeschlossen! 🎉**

