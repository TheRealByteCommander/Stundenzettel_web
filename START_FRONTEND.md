# 🚀 Frontend starten - Schnellanleitung

## Problem: localhost:3000 nicht erreichbar

### Lösung: Frontend-Server starten

**PowerShell (im Projektverzeichnis):**
```powershell
cd frontend
npm start
```

**Wichtig:**
- ✅ Der Server startet automatisch
- ✅ Browser öffnet sich automatisch bei http://localhost:3000
- ✅ Terminal **NICHT schließen** - Server läuft solange Terminal offen ist
- ✅ Bei Änderungen am Code lädt sich die Seite automatisch neu

### Falls der Server nicht startet:

**1. Port prüfen:**
```powershell
netstat -ano | findstr :3000
```

**Falls Port belegt:**
```powershell
# Prozess beenden (PID aus der Ausgabe)
taskkill /PID <PID> /F
```

**2. Dependencies neu installieren:**
```powershell
cd frontend
Remove-Item -Recurse -Force node_modules, package-lock.json -ErrorAction SilentlyContinue
npm install --legacy-peer-deps
npm start
```

**3. Anderen Port verwenden:**
```powershell
cd frontend
$env:PORT=3001
npm start
```
Dann öffnen: http://localhost:3001

### Backend-URL konfigurieren

**Falls Backend auf anderem Port läuft:**

`.env` Datei im `frontend/` Verzeichnis:
```env
REACT_APP_BACKEND_URL=http://localhost:8000
```

**Für lokale Entwicklung standardmäßig:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

## ✅ Erfolgreicher Start

Wenn alles läuft, sehen Sie im Terminal:
```
Compiled successfully!

You can now view frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000
```

## 🆘 Weitere Hilfe

Siehe: [frontend/TROUBLESHOOTING_LOCALHOST.md](frontend/TROUBLESHOOTING_LOCALHOST.md)

