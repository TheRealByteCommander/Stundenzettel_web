# 🔧 Installation - Dependency-Konflikte beheben

## ⚙️ Windows-spezifische Anleitung

**WICHTIG:** Diese Anleitung ist für Windows PowerShell optimiert.

## Problem

Beim `npm install` können Dependency-Konflikte auftreten:
- `react-day-picker@8.10.1` benötigt `date-fns@^2.28.0 || ^3.0.0`, aber es ist `date-fns@4.1.0` installiert
- ESLint-Versionen-Konflikte

## Lösung

Die `package.json` wurde bereits angepasst:
- `date-fns` wurde auf Version `^3.6.0` geändert (kompatibel mit `react-day-picker@8.10.1`)
- ESLint wurde auf Version `^8.57.0` geändert (kompatibel mit `react-scripts@5.0.1`)

## Installation auf Windows

### Option 1: Mit `--legacy-peer-deps` (Empfohlen)

**PowerShell:**
```powershell
cd frontend
npm install --legacy-peer-deps
```

**Command Prompt (CMD):**
```cmd
cd frontend
npm install --legacy-peer-deps
```

### Option 2: Mit Yarn (alternativ)

Da `package.json` bereits `packageManager: yarn` enthält:

**PowerShell/CMD:**
```powershell
cd frontend
yarn install
```

### Option 3: Clean Install (Windows)

Falls Probleme bestehen:

**PowerShell:**
```powershell
cd frontend
Remove-Item -Recurse -Force node_modules, package-lock.json -ErrorAction SilentlyContinue
npm install --legacy-peer-deps
```

**Command Prompt (CMD):**
```cmd
cd frontend
rmdir /s /q node_modules
del package-lock.json
npm install --legacy-peer-deps
```

## Verifizierung

Nach erfolgreicher Installation:

**PowerShell/CMD:**
```powershell
npm start
# Oder
yarn start
```

Die App sollte unter `http://localhost:3000` laufen.

## Windows-spezifische Hinweise

### PowerShell vs. Command Prompt

- **PowerShell** (empfohlen): Unterstützt moderne Befehle
- **Command Prompt**: Verwenden Sie `dir` statt `ls`, `rmdir` statt `rm`

### Pfade auf Windows

- Verwenden Sie **Backslashes** `\` oder **vorwärts Slashes** `/` (beide funktionieren)
- Beispiel: `C:\Users\mschm\Stundenzettel_web\frontend` oder `C:/Users/mschm/Stundenzettel_web/frontend`

### Node.js Installation

Stellen Sie sicher, dass Node.js korrekt installiert ist:

```powershell
node --version
npm --version
```

Sollte `node v18.x.x` oder höher und `npm 8.x.x` oder höher sein.

## Troubleshooting

### Problem: "Cannot find module 'react-day-picker'"

**PowerShell:**
```powershell
cd frontend
Get-ChildItem node_modules | Select-String "react-day-picker"
```

**CMD:**
```cmd
cd frontend
dir node_modules | findstr react-day-picker
```

Falls nicht vorhanden:
```powershell
npm install react-day-picker@8.10.1 --legacy-peer-deps
```

### Problem: "npm: command not found" oder "node: command not found"

Lösung:
1. Node.js von https://nodejs.org/ installieren
2. PowerShell/CMD neu starten
3. Installation verifizieren: `node --version`

### Problem: PowerShell Execution Policy

Falls Scripts nicht ausgeführt werden können:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Problem: ESLint-Fehler beim Build

Die ESLint-Warnungen können ignoriert werden, da sie hauptsächlich Peer-Dependency-Warnungen sind. Der Build sollte trotzdem funktionieren.

### Problem: Date-Funktionen funktionieren nicht

Prüfen Sie die `date-fns` Version:

```powershell
npm list date-fns
```

Sollte `date-fns@3.x.x` sein (nicht 4.x.x).

### Problem: Port 3000 bereits belegt

**PowerShell:**
```powershell
netstat -ano | findstr :3000
# Dann Prozess beenden (PID aus der Ausgabe):
taskkill /PID <PID> /F
```

**Alternative:** Anderen Port verwenden:
```powershell
$env:PORT=3001
npm start
```

### Problem: Lange Pfade (Windows)

Windows kann Probleme mit sehr langen Dateipfaden haben. Falls nötig:

1. Registry-Editor öffnen (`regedit`)
2. Navigieren zu: `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem`
3. `LongPathsEnabled` auf `1` setzen (oder erstellen, Typ: DWORD)
4. Computer neu starten

## Nützliche Windows-Befehle

```powershell
# Aktuelles Verzeichnis anzeigen
pwd
# oder
Get-Location

# Dateien auflisten
Get-ChildItem
# oder
ls

# Verzeichnis wechseln
cd frontend

# Umgebungsvariable setzen (für Session)
$env:REACT_APP_BACKEND_URL="http://localhost:8000"

# Umgebungsvariable permanent setzen (System-weit)
[System.Environment]::SetEnvironmentVariable('REACT_APP_BACKEND_URL', 'http://localhost:8000', 'User')
```

