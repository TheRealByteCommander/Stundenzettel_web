# 🪟 Windows-Installationsanleitung
## Stundenzettel Web - Zeiterfassungssystem für Schmitz Intralogistik GmbH

**Spezielle Anleitung für Windows 10/11**

---

## 📋 Inhaltsverzeichnis

1. [Voraussetzungen](#voraussetzungen)
2. [Software installieren](#software-installieren)
3. [Projekt einrichten](#projekt-einrichten)
4. [Backend konfigurieren](#backend-konfigurieren)
5. [Frontend konfigurieren](#frontend-konfigurieren)
6. [MongoDB einrichten](#mongodb-einrichten)
7. [Anwendung starten](#anwendung-starten)
8. [Troubleshooting](#troubleshooting)

---

## 🔧 Voraussetzungen

### Systemanforderungen

- **Windows 10** (64-bit) oder **Windows 11**
- **RAM:** Mindestens 4GB (8GB empfohlen)
- **Festplattenspeicher:** 5GB freier Speicherplatz
- **Internetverbindung** für Downloads

### Erforderliche Software

1. **Python 3.11+** (https://www.python.org/downloads/)
2. **Node.js 18.x+** (https://nodejs.org/)
3. **MongoDB Community Edition** (https://www.mongodb.com/try/download/community)
4. **Git für Windows** (https://git-scm.com/downloads)
5. **Visual Studio Code** (optional, empfohlen: https://code.visualstudio.com/)

---

## 📦 Software installieren

### 1. Python installieren

1. **Python herunterladen:**
   - Gehen Sie zu: https://www.python.org/downloads/
   - Laden Sie **Python 3.11 oder höher** herunter (64-bit Windows Installer)

2. **Installation durchführen:**
   - ⚠️ **WICHTIG:** Aktivieren Sie **"Add Python to PATH"** während der Installation!
   - Klicken Sie auf "Install Now"
   - Warten Sie, bis die Installation abgeschlossen ist

3. **Installation verifizieren:**
   - Öffnen Sie **PowerShell** (als Administrator)
   - Führen Sie aus:
   ```powershell
   python --version
   pip --version
   ```
   - Sollte `Python 3.11.x` oder höher anzeigen

### 2. Node.js installieren

1. **Node.js herunterladen:**
   - Gehen Sie zu: https://nodejs.org/
   - Laden Sie die **LTS-Version** (Long Term Support) herunter
   - Wählen Sie den **Windows Installer (.msi)**

2. **Installation durchführen:**
   - Doppelklicken Sie auf die heruntergeladene `.msi` Datei
   - Folgen Sie dem Installations-Assistenten
   - ⚠️ **WICHTIG:** Aktivieren Sie "Automatically install the necessary tools"

3. **Installation verifizieren:**
   ```powershell
   node --version
   npm --version
   ```
   - Sollte `v18.x.x` oder höher für Node.js anzeigen
   - Sollte `9.x.x` oder höher für npm anzeigen

### 3. MongoDB installieren

1. **MongoDB herunterladen:**
   - Gehen Sie zu: https://www.mongodb.com/try/download/community
   - Wählen Sie:
     - **Version:** 7.0 oder neuer
     - **Platform:** Windows
     - **Package:** MSI

2. **Installation durchführen:**
   - Doppelklicken Sie auf die heruntergeladene `.msi` Datei
   - Wählen Sie **"Complete"** Installation
   - ⚠️ **WICHTIG:** Aktivieren Sie **"Install MongoDB as a Service"**
   - Wählen Sie **"Run service as Network Service user"**
   - **Install MongoDB Compass** aktivieren (GUI-Tool, empfohlen)

3. **Installation verifizieren:**
   ```powershell
   mongod --version
   ```
   - Sollte die MongoDB-Version anzeigen

4. **MongoDB Service starten:**
   ```powershell
   # Als Administrator:
   net start MongoDB
   
   # Status prüfen:
   Get-Service MongoDB
   ```

### 4. Git installieren

1. **Git herunterladen:**
   - Gehen Sie zu: https://git-scm.com/downloads
   - Laden Sie **Git for Windows** herunter

2. **Installation durchführen:**
   - Doppelklicken Sie auf die Installer-Datei
   - Verwenden Sie die Standard-Einstellungen
   - Wählen Sie **"Git from the command line and also from 3rd-party software"**

3. **Installation verifizieren:**
   ```powershell
   git --version
   ```

---

## 🚀 Projekt einrichten

### 1. Projekt klonen

**PowerShell:**
```powershell
# Navigieren Sie zu Ihrem gewünschten Verzeichnis (z.B. Dokumente)
cd C:\Users\IhrBenutzername\Documents

# Projekt klonen
git clone https://github.com/TheRealByteCommander/Stundenzettel_web.git

# In Projekt-Verzeichnis wechseln
cd Stundenzettel_web
```

**Alternative: ZIP herunterladen:**
- GitHub Repository: https://github.com/TheRealByteCommander/Stundenzettel_web
- **Code** → **Download ZIP**
- ZIP-Datei entpacken

### 2. Backend einrichten

**PowerShell:**
```powershell
# In Backend-Verzeichnis wechseln
cd backend

# Virtual Environment erstellen
python -m venv venv

# Virtual Environment aktivieren
.\venv\Scripts\Activate.ps1

# Falls Fehler "execution policy": Erst ausführen:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Dependencies installieren
pip install --upgrade pip
pip install -r requirements.txt
```

**Command Prompt (CMD) - Alternative:**
```cmd
cd backend
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Frontend einrichten

**PowerShell:**
```powershell
# In Frontend-Verzeichnis wechseln
cd ..\frontend

# Dependencies installieren (mit --legacy-peer-deps wegen Konflikten)
npm install --legacy-peer-deps
```

---

## ⚙️ Backend konfigurieren

### 1. .env Datei erstellen

**PowerShell:**
```powershell
cd backend

# .env Datei erstellen
Set-Content .env "MONGO_URL=mongodb://localhost:27017"
Add-Content .env "DB_NAME=stundenzettel"
Add-Content .env "SECRET_KEY=Ihr-Sehr-Geheimer-Secret-Key-Hier-Mindestens-32-Zeichen-Lang"
Add-Content .env "LOCAL_RECEIPTS_PATH=C:\Reisekosten_Belege"
```

**Oder manuell:**
1. Erstellen Sie eine Datei `.env` im `backend/` Ordner
2. Fügen Sie folgenden Inhalt ein:

```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=stundenzettel
SECRET_KEY=Ihr-Sehr-Geheimer-Secret-Key-Hier-Mindestens-32-Zeichen-Lang

# Lokaler Speicher für Reisekosten-Belege (DSGVO-konform)
LOCAL_RECEIPTS_PATH=C:\Reisekosten_Belege

# Ollama LLM (falls verwendet)
OLLAMA_BASE_URL=http://192.168.1.100:11434
OLLAMA_MODEL=llama3.2
```

### 2. Verschlüsselungsschlüssel generieren

```powershell
# Mit aktiviertem venv:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Kopieren Sie den generierten Schlüssel und fügen Sie ihn in `.env` ein:
```env
ENCRYPTION_KEY=<generierter-schlüssel-hier>
```

### 3. Lokales Verzeichnis für Belege erstellen

```powershell
# Erstellen Sie das Verzeichnis (falls nicht vorhanden)
New-Item -ItemType Directory -Force -Path "C:\Reisekosten_Belege"
New-Item -ItemType Directory -Force -Path "C:\Reisekosten_Belege\signed_timesheets"
```

---

## 🎨 Frontend konfigurieren

### 1. .env Datei erstellen

**PowerShell:**
```powershell
cd ..\frontend

# .env Datei erstellen
Set-Content .env "REACT_APP_BACKEND_URL=http://localhost:8000"
```

**Oder manuell:**
Erstellen Sie eine Datei `.env` im `frontend/` Ordner:
```env
REACT_APP_BACKEND_URL=http://localhost:8000
```

---

## 🗄️ MongoDB einrichten

### 1. MongoDB Service starten

**PowerShell (als Administrator):**
```powershell
net start MongoDB
```

**Status prüfen:**
```powershell
Get-Service MongoDB
```

Sollte `Running` anzeigen.

### 2. MongoDB Shell testen

```powershell
mongosh
```

Sollte eine MongoDB-Shell öffnen. Verlassen Sie mit `exit`.

### 3. MongoDB Compass (Optional)

- Öffnen Sie **MongoDB Compass** (wurde bei Installation installiert)
- Verbinden Sie sich mit: `mongodb://localhost:27017`
- Überprüfen Sie, dass die Verbindung funktioniert

---

## ▶️ Anwendung starten

### 1. Terminal 1: Backend starten

**PowerShell:**
```powershell
# In Backend-Verzeichnis
cd C:\Users\IhrBenutzername\Documents\Stundenzettel_web\backend

# Virtual Environment aktivieren
.\venv\Scripts\Activate.ps1

# Server starten
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

Sie sollten sehen:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 2. Terminal 2: Frontend starten

**PowerShell (neues Fenster):**
```powershell
# In Frontend-Verzeichnis
cd C:\Users\IhrBenutzername\Documents\Stundenzettel_web\frontend

# Development Server starten
npm start
```

Browser öffnet sich automatisch unter `http://localhost:3000`

### 3. Erste Anmeldung

- **URL:** http://localhost:3000
- **E-Mail:** admin@schmitz-intralogistik.de
- **Passwort:** admin123
- ⚠️ **WICHTIG:** Ändern Sie das Passwort sofort!

---

## 🔍 Troubleshooting

### Problem: "python: command not found"

**Lösung:**
1. Python wurde nicht zu PATH hinzugefügt
2. **Lösung A:** Python neu installieren mit "Add to PATH" Option
3. **Lösung B:** Manuell zu PATH hinzufügen:
   - Systemsteuerung → System → Erweiterte Systemeinstellungen
   - Umgebungsvariablen → Systemvariablen → Path → Bearbeiten
   - Fügen Sie hinzu: `C:\Python311\` und `C:\Python311\Scripts\`
   - PowerShell/CMD neu starten

### Problem: "npm: command not found"

**Lösung:**
1. Node.js wurde nicht korrekt installiert
2. PowerShell/CMD neu starten
3. Installation verifizieren: `node --version`

### Problem: "execution policy" Fehler in PowerShell

**Lösung:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Problem: MongoDB Service startet nicht

**Lösung:**
```powershell
# Als Administrator:
# Service stoppen
net stop MongoDB

# Service starten
net start MongoDB

# Status prüfen
Get-Service MongoDB

# Eventuell neu installieren oder Logs prüfen:
Get-EventLog -LogName Application -Source MongoDB -Newest 10
```

### Problem: Port 8000 oder 3000 bereits belegt

**Lösung:**
```powershell
# Prozess finden, der Port 8000 verwendet:
netstat -ano | findstr :8000

# Prozess beenden (PID aus der Ausgabe):
taskkill /PID <PID> /F
```

### Problem: "Module not found" Fehler

**Lösung:**
```powershell
# Backend:
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Frontend:
cd ..\frontend
Remove-Item -Recurse -Force node_modules
npm install --legacy-peer-deps
```

### Problem: "Cannot connect to MongoDB"

**Lösung:**
1. MongoDB Service prüfen:
   ```powershell
   Get-Service MongoDB
   ```

2. MongoDB starten:
   ```powershell
   net start MongoDB
   ```

3. Verbindung testen:
   ```powershell
   mongosh
   ```

### Problem: Lange Dateipfade

Windows kann Probleme mit sehr langen Pfaden haben:

**Lösung:**
1. Registry-Editor öffnen (`regedit`)
2. Navigieren zu: `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem`
3. `LongPathsEnabled` auf `1` setzen (DWORD erstellen falls nicht vorhanden)
4. Computer neu starten

---

## 📝 Nützliche Windows-Befehle

### PowerShell

```powershell
# Aktuelles Verzeichnis anzeigen
Get-Location
# oder
pwd

# Dateien auflisten
Get-ChildItem
# oder
ls

# Verzeichnis erstellen
New-Item -ItemType Directory -Path "C:\NeuerOrdner"

# Datei erstellen
Set-Content -Path "datei.txt" -Value "Inhalt"

# Umgebungsvariable setzen (temporär)
$env:REACT_APP_BACKEND_URL="http://localhost:8000"

# Prozess beenden
Stop-Process -Name "node" -Force
```

### Command Prompt (CMD)

```cmd
# Aktuelles Verzeichnis
cd

# Dateien auflisten
dir

# Verzeichnis erstellen
mkdir C:\NeuerOrdner

# Datei erstellen
echo Inhalt > datei.txt

# Umgebungsvariable setzen (temporär)
set REACT_APP_BACKEND_URL=http://localhost:8000

# Prozess beenden
taskkill /IM node.exe /F
```

---

## ✅ Installations-Checkliste

- [ ] Python 3.11+ installiert und zu PATH hinzugefügt
- [ ] Node.js 18+ installiert
- [ ] MongoDB installiert und Service läuft
- [ ] Git installiert
- [ ] Projekt geklont/heruntergeladen
- [ ] Backend Virtual Environment erstellt
- [ ] Backend Dependencies installiert (`pip install -r requirements.txt`)
- [ ] Frontend Dependencies installiert (`npm install --legacy-peer-deps`)
- [ ] Backend `.env` Datei erstellt und konfiguriert
- [ ] Frontend `.env` Datei erstellt
- [ ] MongoDB Service gestartet
- [ ] Backend läuft auf Port 8000
- [ ] Frontend läuft auf Port 3000
- [ ] Erste Anmeldung erfolgreich

---

**Installation auf Windows abgeschlossen! 🎉**

Bei weiteren Fragen siehe [INSTALLATION_COMPLETE.md](INSTALLATION_COMPLETE.md) oder [frontend/INSTALLATION_FIX.md](frontend/INSTALLATION_FIX.md).

