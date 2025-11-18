# 🚀 Frontend starten - Schnellanleitung

## Frontend-Server starten (Vite)

**PowerShell (im Projektverzeichnis):**
```powershell
cd frontend
npm install
npm run dev
```

**Wichtig:**
- ✅ Der Server startet automatisch
- ✅ Browser öffnet sich automatisch bei http://localhost:5173
- ✅ Terminal **NICHT schließen** - Server läuft solange Terminal offen ist
- ✅ Bei Änderungen am Code lädt sich die Seite automatisch neu (Hot Module Replacement)

### Falls der Server nicht startet:

**1. Port prüfen:**
```powershell
netstat -ano | findstr :5173
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
npm install
npm run dev
```

**3. Anderen Port verwenden:**
```powershell
cd frontend
$env:PORT=5174
npm run dev
```
Dann öffnen: http://localhost:5174

### Backend-URL konfigurieren

**Falls Backend auf anderem Port läuft:**

`.env` Datei im `frontend/` Verzeichnis:
```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_DEFAULT_ADMIN_EMAIL=admin@schmitz-intralogistik.de
VITE_DEFAULT_ADMIN_PASSWORD=admin123
```

**Für lokale Entwicklung standardmäßig:**
- Frontend: http://localhost:5173 (Vite Dev-Server)
- Backend: http://localhost:8000/api

## ✅ Erfolgreicher Start

Wenn alles läuft, sehen Sie im Terminal:
```
  VITE v7.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

## 🧪 Tests ausführen

**E2E-Tests (Playwright):**
```powershell
cd frontend
npm run test:e2e
```

**E2E-Tests mit UI:**
```powershell
npm run test:e2e:ui
```

## 🆘 Weitere Hilfe

Siehe: [frontend/README.md](frontend/README.md)

