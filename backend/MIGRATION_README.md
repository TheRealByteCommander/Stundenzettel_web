# 📦 Datenbank-Migrations-Tool

Dieses Tool ermöglicht die Migration von Daten aus einer Vorgänger-Version der Anwendung in die neue Datenbankstruktur.

## 🔒 Sicherheit

**WICHTIG:** Das Tool ist so konzipiert, dass die Source-Datenbank **niemals verändert wird**:
- ✅ Nur **READ-Operationen** (SELECT, find)
- ✅ **Read-Only-Modus** für MySQL (falls möglich)
- ✅ **Keine INSERT/UPDATE/DELETE** auf Source-DB
- ✅ **Idempotent**: Kann mehrfach ausgeführt werden (überspringt bereits vorhandene Daten)

## 📋 Voraussetzungen

- Python 3.11+
- Zugriff auf Source-Datenbank (read-only)
- Zugriff auf Target-Datenbank (neue MongoDB)
- Installierte Abhängigkeiten:
  ```bash
  pip install pymongo motor mysql-connector-python
  ```

## 🚀 Verwendung

### Option 1: Kommandozeile

#### Migration von MongoDB Source

```bash
cd backend
python migration_tool.py \
  --source-type mongo \
  --source-host localhost \
  --source-port 27017 \
  --source-database alte_db \
  --target-mongo-url mongodb://localhost:27017 \
  --target-db-name stundenzettel
```

#### Migration von MySQL Source

```bash
python migration_tool.py \
  --source-type mysql \
  --source-host localhost \
  --source-port 3306 \
  --source-database alte_db \
  --source-user db_user \
  --source-password db_password \
  --target-mongo-url mongodb://localhost:27017 \
  --target-db-name stundenzettel
```

#### Mit Mapping-Konfiguration

Erstellen Sie eine `migration_config.json`:

```json
{
  "mappings": {
    "users": {
      "collection": "benutzer",
      "field_mappings": {
        "email": "Email",
        "name": "Name",
        "password_hash": "Passwort"
      }
    },
    "timesheets": {
      "collection": "stundenzettel",
      "field_mappings": {
        "user_id": "BenutzerID",
        "week_start": "Wochenanfang"
      }
    }
  }
}
```

Dann:

```bash
python migration_tool.py \
  --source-type mongo \
  --source-database alte_db \
  --target-db-name stundenzettel \
  --mapping-config migration_config.json
```

### Option 2: Python-Script

```python
import asyncio
from migration_tool import DatabaseMigration

async def migrate():
    # Source-DB Konfiguration
    source_config = {
        'type': 'mysql',  # oder 'mongo'
        'host': 'localhost',
        'port': 3306,
        'database': 'alte_db',
        'user': 'db_user',
        'password': 'db_password'
    }
    
    # Target-DB Konfiguration
    target_config = {
        'mongo_url': 'mongodb://localhost:27017',
        'db_name': 'stundenzettel'
    }
    
    # Mapping-Konfiguration (optional)
    mapping_config = {
        'users_collection': 'benutzer',
        'users_columns': {
            'email': 'Email',
            'name': 'Name'
        }
    }
    
    # Migration durchführen
    migration = DatabaseMigration(source_config, target_config)
    results = await migration.migrate_all(mapping_config=mapping_config)
    
    print(f"Migration abgeschlossen: {results}")

asyncio.run(migrate())
```

## 📊 Unterstützte Datenstrukturen

### Users (Benutzer)

**Source → Target Mapping:**

| Source (alt) | Target (neu) |
|--------------|--------------|
| `email` / `Email` | `email` |
| `name` / `Name` | `name` |
| `password_hash` / `password` | `hashed_password` |
| `is_admin` / `IsAdmin` | `role` ("admin" oder "user") |
| `weekly_hours` / `weeklyHours` | `weekly_hours` (default: 40.0) |

**Neue Felder:**
- `role`: "user", "admin", oder "accounting"
- `two_fa_enabled`: false (Standard)
- `two_fa_secret`: null (Standard)

### Timesheets (Stundenzettel)

**Source → Target Mapping:**

| Source (alt) | Target (neu) |
|--------------|--------------|
| `id` / `_id` | `id` |
| `user_id` / `userId` | `user_id` |
| `user_name` / `userName` | `user_name` |
| `week_start` / `weekStart` | `week_start` |
| `week_end` / `weekEnd` | `week_end` |
| `entries` / `Entries` | `entries` |
| `status` | `status` ("draft", "sent", "approved") |

### Travel Expenses (Reisekosten)

Falls in der alten DB vorhanden, werden Reisekosten ebenfalls migriert.

## ⚙️ Mapping-Konfiguration

Die Mapping-Konfiguration ermöglicht die Anpassung an verschiedene Datenbankstrukturen:

```json
{
  "description": "Custom Mapping",
  "mappings": {
    "users": {
      "collection": "benutzer_tabelle",
      "field_mappings": {
        "email": "EmailAdresse",
        "name": "VollständigerName",
        "password_hash": "PasswortHash",
        "is_admin": "IstAdmin"
      }
    },
    "timesheets": {
      "collection": "stundenzettel_sammlung",
      "field_mappings": {
        "user_id": "Benutzer_ID",
        "week_start": "Wochenbeginn",
        "entries": "Einträge"
      }
    }
  },
  "mysql_mappings": {
    "users": {
      "table": "users",
      "columns": {
        "email": "email_column",
        "name": "name_column",
        "password": "password_column",
        "is_admin": "admin_flag"
      }
    }
  }
}
```

## 🔍 Validierung

Nach der Migration können Sie die Daten validieren:

```python
from motor.motor_asyncio import AsyncIOMotorClient

async def validate_migration():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['stundenzettel']
    
    users_count = await db.users.count_documents({})
    timesheets_count = await db.weekly_timesheets.count_documents({})
    
    print(f"Users: {users_count}")
    print(f"Timesheets: {timesheets_count}")
```

## ⚠️ Wichtige Hinweise

1. **Backup erstellen:** Vor der Migration immer ein Backup der Target-DB erstellen!

2. **Read-Only prüfen:** Das Tool prüft automatisch, ob die Source-DB read-only ist, aber es ist sicherer, die Source-DB manuell auf read-only zu setzen.

3. **Duplikate:** Das Tool überspringt automatisch bereits vorhandene Einträge (basierend auf ID oder Email).

4. **Inkrementelle Migration:** Das Tool kann mehrfach ausgeführt werden - bereits migrierte Daten werden übersprungen.

5. **Fehlerbehandlung:** Bei Fehlern wird der Datensatz übersprungen und in der Zusammenfassung aufgeführt.

## 🐛 Fehlerbehebung

### "Connection refused" / "Cannot connect to database"

- Überprüfen Sie Host, Port und Zugangsdaten
- Stellen Sie sicher, dass die Datenbank erreichbar ist
- Für MySQL: Prüfen Sie, ob der User remote-Zugriff hat (oder verwenden Sie localhost)

### "Permission denied"

- Überprüfen Sie Datenbank-Berechtigungen
- Für MySQL: User braucht SELECT-Recht
- Für MongoDB: User braucht readRecht

### "Collection/Table not found"

- Überprüfen Sie die Namen in der Mapping-Konfiguration
- Prüfen Sie, ob die Collection/Tabelle existiert

### "Field mapping error"

- Überprüfen Sie die Mapping-Konfiguration
- Stellen Sie sicher, dass alle erforderlichen Felder gemappt sind

## 📝 Beispiel-Workflow

1. **Backup erstellen:**
   ```bash
   # Target-DB Backup
   mongodump --uri="mongodb://localhost:27017/stundenzettel" --out=/backup/pre_migration
   ```

2. **Mapping-Konfiguration erstellen:**
   - Analysieren Sie die Source-DB-Struktur
   - Erstellen Sie `migration_config.json`

3. **Test-Migration (kleine Datenmenge):**
   ```bash
   python migration_tool.py \
     --source-type mysql \
     --source-database alte_db \
     --target-db-name stundenzettel_test \
     --mapping-config migration_config.json
   ```

4. **Migration prüfen:**
   - Daten in Test-DB überprüfen
   - Validierung durchführen

5. **Vollständige Migration:**
   ```bash
   python migration_tool.py \
     --source-type mysql \
     --source-database alte_db \
     --target-db-name stundenzettel \
     --mapping-config migration_config.json
   ```

6. **Nach der Migration:**
   - Daten in der neuen DB überprüfen
   - Test-Login durchführen
   - Funktionen testen

## 🔐 Sicherheit: Source-DB Read-Only setzen

### MySQL Read-Only setzen

```sql
-- Als root
SET GLOBAL read_only = ON;
SET GLOBAL super_read_only = ON;

-- Prüfen
SHOW VARIABLES LIKE 'read_only';
```

### MongoDB Read-Only User erstellen

```javascript
// In MongoDB Shell
use admin
db.createUser({
  user: "migration_readonly",
  pwd: "SicheresPasswort",
  roles: [{ role: "read", db: "alte_db" }]
})
```

---

**Migration erfolgreich durchgeführt! 🎉**

Bei Fragen oder Problemen siehe Fehlerbehebung oder kontaktieren Sie den Support.

