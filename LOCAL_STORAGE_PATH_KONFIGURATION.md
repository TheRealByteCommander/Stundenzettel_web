# 📁 Lokaler Speicherpfad konfigurieren - Office-Rechner

## Wo wird der Pfad eingetragen?

Der Pfad zum Office-Rechner wird in der **`.env` Datei im `backend/` Verzeichnis** eingetragen.

## Konfiguration

### 1. Backend `.env` Datei öffnen/bearbeiten

**Pfad:** `backend/.env`

**Fügen Sie folgende Zeile hinzu (oder bearbeiten Sie die vorhandene):**

```env
LOCAL_RECEIPTS_PATH=C:/Reisekosten_Belege
```

### 2. Windows-Beispiele

```env
# Laufwerk C: (Standard)
LOCAL_RECEIPTS_PATH=C:/Reisekosten_Belege

# Anderes Laufwerk
LOCAL_RECEIPTS_PATH=D:/Reisekosten_Belege

# Spezifischer Ordner
LOCAL_RECEIPTS_PATH=C:/Users/IhrBenutzername/Documents/Reisekosten_Belege

# Netzwerkfreigabe (wenn Office-Rechner über Netzwerk erreichbar ist)
LOCAL_RECEIPTS_PATH=\\192.168.1.100\Reisekosten_Belege
```

### 3. Linux/Mac-Beispiele

```env
# Linux
LOCAL_RECEIPTS_PATH=/var/receipts

# Mac
LOCAL_RECEIPTS_PATH=/Users/IhrBenutzername/Documents/Reisekosten_Belege

# Gemounteter Netzwerkpfad
LOCAL_RECEIPTS_PATH=/mnt/office-rechner/receipts
```

## Vollständige `.env` Beispiel-Datei

```env
# ============================================
# DATENBANK
# ============================================
MONGO_URL=mongodb://localhost:27017
DB_NAME=stundenzettel

# ============================================
# SICHERHEIT
# ============================================
SECRET_KEY=Ihr-Sehr-Geheimer-Secret-Key-Hier-Mindestens-32-Zeichen-Lang

# Verschlüsselungsschlüssel für DSGVO-Compliance
ENCRYPTION_KEY=Ihre-44-Zeichen-Base64-Verschluesselungs-Schluessel-Hier

# ============================================
# REISEKOSTEN-APP - WICHTIG!
# ============================================
# Lokaler Speicherpfad für PDF-Belege
# MUSS auf Office-Rechner zeigen, NICHT Webserver!
# Windows:
LOCAL_RECEIPTS_PATH=C:/Reisekosten_Belege
# Linux:
# LOCAL_RECEIPTS_PATH=/var/receipts

# ============================================
# OLLAMA LLM (Optional)
# ============================================
OLLAMA_BASE_URL=http://192.168.1.100:11434
OLLAMA_MODEL=llama3.2
```

## Wichtige Hinweise

### ⚠️ DSGVO-Compliance

- **Der Pfad MUSS auf einen lokalen Office-Rechner zeigen, NICHT auf den Webserver!**
- Das System validiert automatisch, dass der Pfad nicht auf einen Webserver zeigt
- Falls der Pfad ungültig ist, startet der Server nicht (Security-Feature)

### 📂 Verzeichnis wird automatisch erstellt

Falls das Verzeichnis nicht existiert, wird es automatisch erstellt beim Server-Start:

```
INFO: Created local receipts directory: C:/Reisekosten_Belege
```

### 🔒 Verschlüsselung

Alle hochgeladenen PDFs werden automatisch verschlüsselt und in diesem Verzeichnis gespeichert:
- `C:/Reisekosten_Belege/` - Reisekosten-Belege
- `C:/Reisekosten_Belege/signed_timesheets/` - Unterschriebene Stundenzettel

## Netzwerkfreigabe (für verteilte Installation)

Falls der Office-Rechner über das Netzwerk erreichbar ist:

### Windows Netzwerkfreigabe

```env
# Windows UNC-Pfad
LOCAL_RECEIPTS_PATH=\\192.168.1.100\Reisekosten_Belege

# Oder gemapptes Laufwerk
LOCAL_RECEIPTS_PATH=Z:/Reisekosten_Belege
```

### Linux/Mac Netzwerk-Mount

```env
# Gemounteter Netzwerkpfad
LOCAL_RECEIPTS_PATH=/mnt/office-rechner/receipts
```

**Wichtig:** Stellen Sie sicher, dass:
1. Die Netzwerkfreigabe lesbar und beschreibbar ist
2. Der Backend-Server Zugriff auf die Freigabe hat
3. Die Freigabe dauerhaft gemountet/verbunden ist

## Überprüfung

### 1. Pfad in Code prüfen

Der Pfad wird in `backend/server.py` Zeile 41 gelesen:

```python
LOCAL_RECEIPTS_PATH = os.getenv('LOCAL_RECEIPTS_PATH', 'C:/Reisekosten_Belege')
```

### 2. Validierung beim Start

Beim Server-Start wird der Pfad validiert:

```python
is_valid, error_msg = validate_local_storage_path(LOCAL_RECEIPTS_PATH)
if not is_valid:
    logging.error(f"INVALID STORAGE PATH: {error_msg}")
    raise ValueError(f"Invalid storage path: {error_msg}")
```

### 3. Server-Logs prüfen

Nach dem Start sollten Sie in den Logs sehen:

```
INFO: Created local receipts directory: C:/Reisekosten_Belege
```

Oder falls bereits vorhanden:
```
INFO: Using local receipts directory: C:/Reisekosten_Belege
```

## Troubleshooting

### Problem: "INVALID STORAGE PATH: Path appears to be on a webserver"

**Ursache:** Der Pfad zeigt auf einen Webserver (z.B. `/var/www/`, `/usr/share/`)

**Lösung:** Verwenden Sie einen lokalen Pfad auf dem Office-Rechner:

```env
# ❌ Falsch (Webserver)
LOCAL_RECEIPTS_PATH=/var/www/receipts

# ✅ Richtig (lokaler Office-Rechner)
LOCAL_RECEIPTS_PATH=C:/Reisekosten_Belege
```

### Problem: "Could not create local receipts directory"

**Ursache:** Keine Berechtigung zum Erstellen des Verzeichnisses

**Lösung:**
1. Prüfen Sie Berechtigungen
2. Erstellen Sie das Verzeichnis manuell:
   ```powershell
   # Windows
   mkdir C:\Reisekosten_Belege
   ```
3. Prüfen Sie, ob der Backend-Server Schreibrechte hat

### Problem: Pfad funktioniert nicht bei Netzwerkfreigabe

**Lösung:**
1. Prüfen Sie Netzwerkverbindung
2. Testen Sie Zugriff manuell:
   ```powershell
   # Windows
   dir \\192.168.1.100\Reisekosten_Belege
   ```
3. Verwenden Sie gemapptes Laufwerk statt UNC-Pfad

## Zusammenfassung

**Wo eintragen?**
- Datei: `backend/.env`
- Variable: `LOCAL_RECEIPTS_PATH`

**Beispiel:**
```env
LOCAL_RECEIPTS_PATH=C:/Reisekosten_Belege
```

**Nach Änderung:**
- Backend-Server neu starten
- Logs prüfen, ob Pfad erkannt wurde

