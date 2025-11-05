# 🗄️ Datenbank-Architektur - Klarstellung

## ⚠️ WICHTIG: MySQL auf All-inkl.com ist NICHT notwendig für die aktuelle Architektur!

### ✅ Aktuelle Architektur (Python/FastAPI)

**Verwendete Datenbank:**
- **MongoDB** (auf Proxmox Server oder remote/Cloud)
- **NICHT MySQL**

**Warum MongoDB?**
- Flexible Datenstruktur für komplexe Dokumente (Stundenzettel, Reisekosten, Agent-Memory)
- Bessere Performance für JSON-Daten
- Unterstützt Embedded-Dokumente (z.B. Einträge in Stundenzettel)
- Agent-System nutzt MongoDB für Memory-System

**Wo läuft MongoDB?**
- Auf **Proxmox Server** (lokal) ODER
- Remote/Cloud (z.B. MongoDB Atlas)

**Konfiguration:**
```env
# backend/.env (auf Proxmox)
MONGO_URL=mongodb://localhost:27017
# oder remote:
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/stundenzettel
```

---

## ❓ Wann wird MySQL verwendet?

MySQL wird **NUR** in zwei Fällen verwendet:

### 1. Migration (einmalig)

**Zweck:** Import von Daten aus einer Vorgänger-Version

**Wann:**
- Einmalige Migration von alter MySQL-Datenbank zur neuen MongoDB
- Migration-Tool liest aus alter MySQL-DB (read-only)
- Daten werden in neue MongoDB importiert

**Wie:**
```bash
# Migration-Tool
python migration_tool.py \
  --source-type mysql \
  --source-host <alte-mysql-host> \
  --source-database <alte-db> \
  --target-mongo-url mongodb://localhost:27017 \
  --target-db-name stundenzettel
```

**Nach Migration:**
- MySQL wird nicht mehr benötigt
- Alle Daten sind in MongoDB
- Migration-Tool kann gelöscht werden

---

### 2. Legacy PHP-Version (nicht empfohlen)

**Zweck:** Falls Sie die alte PHP-Version aus `webapp/` verwenden

**Wann:**
- Nur wenn Sie wirklich PHP verwenden wollen
- PHP-Version unterstützt NICHT:
  - Agent-System
  - LLM-Integration
  - Automatische Stundenzettel-Verifikation
  - Reisekosten-App mit Agents
  - Urlaubsplaner mit Feiertags-Integration

**MySQL-Konfiguration (nur für Legacy PHP):**
- MySQL-Datenbank auf All-inkl.com
- `webapp/api/config/database.php` konfigurieren
- Legacy PHP-Version nutzt MySQL statt MongoDB

**Empfehlung:**
- ❌ **NICHT verwenden** - PHP-Version ist Legacy
- ✅ Verwenden Sie die aktuelle Python/FastAPI-Version auf Proxmox

---

## 📊 Zusammenfassung: Datenbank-Verwendung

| Szenario | Datenbank | Wo | Wann nötig? |
|----------|-----------|-----|-------------|
| **Aktuelle Architektur** | MongoDB | Proxmox (oder remote) | ✅ Immer |
| **Migration** | MySQL (Source) | Alte DB (read-only) | ⚠️ Einmalig |
| **Legacy PHP** | MySQL | All-inkl.com | ❌ Nicht empfohlen |

---

## ❌ Häufige Fehler vermeiden

### ❌ FALSCH: MySQL auf All-inkl für aktuelle Architektur

**Problem:**
- Aktuelle Python/FastAPI-Version nutzt MongoDB
- MySQL wird nicht erkannt
- Backend kann nicht starten

**Lösung:**
- MongoDB auf Proxmox installieren
- Oder MongoDB Atlas (Cloud) verwenden
- `.env` Datei: `MONGO_URL=mongodb://...`

### ❌ FALSCH: Backend auf All-inkl installieren

**Problem:**
- All-inkl unterstützt kein Python/FastAPI
- MongoDB nicht verfügbar
- Agents können nicht laufen

**Lösung:**
- Backend auf Proxmox installieren
- Frontend auf All-inkl (nur statische Dateien)

### ✅ RICHTIG: Architektur

```
Frontend (All-inkl) → Backend (Proxmox) → MongoDB (Proxmox)
```

**Keine MySQL-Datenbank auf All-inkl nötig!**

---

## 🔍 MySQL-Referenzen im Code

**MySQL wird nur verwendet in:**
1. `backend/migration_tool.py` - Migration von alter MySQL-DB
2. `backend/requirements.txt` - `mysql-connector-python` (nur für Migration)
3. `webapp/` - Legacy PHP-Version (nicht aktuell)

**NICHT verwendet in:**
- `backend/server.py` - Nutzt nur MongoDB
- Aktuelle Architektur - Nutzt nur MongoDB

---

## ✅ Checkliste: Was ist nötig?

### Für aktuelle Architektur:

- [x] **MongoDB** auf Proxmox installieren
- [ ] MySQL auf All-inkl - **NICHT nötig!**
- [ ] PHP auf All-inkl - **NICHT nötig!** (nur für Frontend statische Dateien)

### Für Migration (einmalig):

- [ ] Zugriff auf alte MySQL-Datenbank (read-only)
- [ ] Migration-Tool ausführen
- [ ] Nach Migration: MySQL nicht mehr nötig

### Für Legacy PHP (nicht empfohlen):

- [ ] MySQL-Datenbank auf All-inkl
- [ ] PHP-Version installieren
- [ ] Alle neuen Features fehlen!

---

## 📚 Weitere Informationen

- **Installationsanleitung:** `INSTALLATION_COMPLETE_CORRECT.md`
- **Architektur:** `ARCHITEKTUR_ALL_INKL_PROXMOX.md`
- **Migration:** `MIGRATION_GUIDE.md`

