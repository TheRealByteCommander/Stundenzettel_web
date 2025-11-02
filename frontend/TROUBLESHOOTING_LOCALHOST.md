# 🔧 Troubleshooting: localhost:3000 nicht erreichbar

## Schnelle Diagnose-Schritte

### 1. Prüfen, ob der Server gestartet wurde

**PowerShell:**
```powershell
# Prüfen, ob Node.js-Prozesse laufen
Get-Process | Where-Object {$_.ProcessName -like "*node*"}

# Prüfen, ob Port 3000 belegt ist
netstat -ano | findstr :3000
```

**Falls Port belegt ist:**
```powershell
# Prozess finden und beenden (PID aus netstat Output)
taskkill /PID <PID> /F
```

### 2. Frontend-Server starten

**PowerShell:**
```powershell
cd frontend
npm start
```

**Wichtig:** Der Server sollte automatisch den Browser öffnen. Falls nicht:
- Öffnen Sie manuell: http://localhost:3000
- Prüfen Sie die Terminal-Ausgabe auf Fehlermeldungen

### 3. Häufige Probleme und Lösungen

#### Problem: "npm start" startet nicht

**Lösung:**
```powershell
# Prüfen, ob node_modules vollständig installiert ist
cd frontend
Test-Path node_modules\.bin\craco.cmd

# Falls False, Dependencies neu installieren:
Remove-Item -Recurse -Force node_modules, package-lock.json -ErrorAction SilentlyContinue
npm install --legacy-peer-deps
```

#### Problem: "Cannot find module" Fehler

**Lösung:**
```powershell
cd frontend
npm install --legacy-peer-deps
```

#### Problem: Port 3000 bereits belegt

**Lösung A - Port freigeben:**
```powershell
# Prozess finden
netstat -ano | findstr :3000

# Prozess beenden (PID aus der Ausgabe)
taskkill /PID <PID> /F
```

**Lösung B - Anderen Port verwenden:**
```powershell
# Temporär für diese Session
$env:PORT=3001
npm start

# Oder dauerhaft in .env Datei:
Set-Content .env "PORT=3001"
```

#### Problem: "EADDRINUSE" Fehler

**Lösung:**
Ein anderer Prozess nutzt Port 3000. Beenden Sie alle Node.js-Prozesse:

```powershell
# Alle Node.js-Prozesse beenden
Get-Process | Where-Object {$_.ProcessName -like "*node*"} | Stop-Process -Force

# Oder nur den spezifischen Port befreien (siehe oben)
```

#### Problem: Firewall blockiert Verbindung

**Lösung:**
Windows Firewall-Regel erstellen:

```powershell
# Als Administrator:
New-NetFirewallRule -DisplayName "Node.js Dev Server" -Direction Inbound -LocalPort 3000 -Protocol TCP -Action Allow
```

#### Problem: Browser zeigt "Verbindung verweigert"

**Prüfliste:**
1. ✅ Server läuft? (Terminal zeigt "Compiled successfully!")
2. ✅ Port 3000 nicht belegt? (`netstat -ano | findstr :3000`)
3. ✅ Firewall blockiert nicht?
4. ✅ Korrekte URL? (`http://localhost:3000` nicht `https://`)

**Test:**
```powershell
# Test ob Server läuft
Test-NetConnection -ComputerName localhost -Port 3000
```

Sollte `TcpTestSucceeded : True` anzeigen.

#### Problem: "ERR_CONNECTION_REFUSED" im Browser

**Mögliche Ursachen:**
1. Server wurde nicht gestartet
2. Server ist abgestürzt
3. Falscher Port

**Lösung:**
```powershell
# 1. Server neu starten
cd frontend
npm start

# 2. Terminal-Ausgabe prüfen auf Fehler
# 3. Browser-Cache leeren (Strg+Shift+R)
```

### 4. Debug-Modus aktivieren

**PowerShell:**
```powershell
cd frontend
$env:DEBUG="*"
npm start
```

Dies zeigt detaillierte Logs.

### 5. Clean Build

Falls nichts hilft, komplett neu aufsetzen:

```powershell
cd frontend

# Alles löschen
Remove-Item -Recurse -Force node_modules, package-lock.json, build -ErrorAction SilentlyContinue

# Neu installieren
npm install --legacy-peer-deps

# Cache leeren
npm cache clean --force

# Server starten
npm start
```

### 6. Alternative: Yarn verwenden

Falls npm Probleme macht:

```powershell
cd frontend
yarn install
yarn start
```

### 7. Port ändern (permanente Lösung)

**In `package.json` ändern:**
```json
{
  "scripts": {
    "start": "set PORT=3001 && craco start"
  }
}
```

**Oder `.env` Datei erstellen:**
```env
PORT=3001
```

### 8. Prüfen der Backend-Verbindung

Falls Frontend startet, aber Backend-Fehler zeigt:

```powershell
# .env Datei prüfen
Get-Content .env

# Sollte enthalten:
# REACT_APP_BACKEND_URL=http://localhost:8000

# Falls nicht vorhanden, erstellen:
Set-Content .env "REACT_APP_BACKEND_URL=http://localhost:8000"
```

## Systematische Fehlersuche

### Schritt 1: Basis-Prüfungen
```powershell
# Im frontend-Verzeichnis:
cd frontend

# 1. Node.js Version
node --version  # Sollte v18.x.x oder höher sein

# 2. npm Version
npm --version  # Sollte 8.x.x oder höher sein

# 3. Dependencies installiert?
Test-Path node_modules  # Sollte True sein

# 4. craco installiert?
Test-Path node_modules\.bin\craco.cmd  # Sollte True sein
```

### Schritt 2: Server starten und Output prüfen
```powershell
cd frontend
npm start
```

**Erwartete Ausgabe:**
```
Compiled successfully!

You can now view frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000

Note that the development build is not optimized.
```

**Falls Fehler auftreten:**
- Kopieren Sie die Fehlermeldung
- Prüfen Sie, ob es Build-Fehler sind oder Runtime-Fehler
- Siehe Abschnitt "Häufige Fehler" unten

### Schritt 3: Browser testen
1. Öffnen Sie http://localhost:3000 manuell
2. Prüfen Sie Browser-Console (F12 → Console)
3. Prüfen Sie Network-Tab (F12 → Network)

## Häufige Fehlermeldungen

### "Error: listen EADDRINUSE: address already in use :::3000"
**Lösung:** Port ist belegt, siehe "Port 3000 bereits belegt"

### "Module not found: Can't resolve '...'"
**Lösung:** 
```powershell
npm install --legacy-peer-deps
```

### "Cannot find module 'react-scripts'"
**Lösung:**
```powershell
npm install react-scripts --legacy-peer-deps
```

### "ERR_OSSL_EVP_UNSUPPORTED"
**Lösung:**
```powershell
$env:NODE_OPTIONS="--openssl-legacy-provider"
npm start
```

### "Failed to compile"
**Lösung:** 
- Terminal-Ausgabe prüfen
- Fehler-spezifische Lösung suchen
- Clean Build durchführen (siehe oben)

## Support

Falls nichts hilft:
1. Terminal-Ausgabe komplett kopieren
2. Browser-Console-Fehler kopieren (F12)
3. `package.json` und `.env` Dateien prüfen
4. System-Informationen:
   ```powershell
   node --version
   npm --version
   Get-ComputerInfo | Select-Object WindowsVersion, OsArchitecture
   ```

