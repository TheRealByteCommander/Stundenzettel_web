# 🔐 Login-Problem beheben

## Problem: Login funktioniert nicht

### Schnelle Diagnose

**1. Backend-Server prüfen:**

```powershell
# Prüfen, ob Backend auf Port 8000 läuft
netstat -ano | findstr :8000
```

**Falls Port 8000 leer ist:** Backend-Server ist nicht gestartet!

### Lösung: Backend-Server starten

**PowerShell (neues Terminal-Fenster):**

```powershell
# Navigieren Sie zum Backend-Verzeichnis
cd C:\Users\mschm\Stundenzettel_web\backend

# Virtual Environment aktivieren
.\venv\Scripts\Activate.ps1

# Server starten
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

**Erwartete Ausgabe:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 2. Backend-URL prüfen

**Prüfen Sie die `.env` Datei im `frontend/` Verzeichnis:**

```powershell
cd C:\Users\mschm\Stundenzettel_web\frontend
Get-Content .env
```

**Sollte enthalten:**
```env
REACT_APP_BACKEND_URL=http://localhost:8000
```

**Falls nicht vorhanden oder falsch:**
```powershell
Set-Content .env "REACT_APP_BACKEND_URL=http://localhost:8000"
```

**Wichtig:** Frontend-Server nach Änderung der `.env` Datei neu starten!

### 3. Browser-Konsole prüfen

1. Öffnen Sie http://localhost:3000
2. Drücken Sie **F12** (Developer Tools)
3. Gehen Sie zum Tab **Console**
4. Versuchen Sie sich einzuloggen
5. Prüfen Sie Fehlermeldungen (z.B. "Network Error", "Connection refused", etc.)

### 4. Netzwerk-Tab prüfen

1. Öffnen Sie **F12** → Tab **Network**
2. Versuchen Sie sich einzuloggen
3. Prüfen Sie die Request zu `/api/auth/login`
4. Status sollte **200** sein, nicht **404** oder **500**

## Häufige Probleme

### Problem 1: "Network Error" oder "Connection refused"

**Ursache:** Backend-Server läuft nicht

**Lösung:**
- Backend-Server starten (siehe oben)
- Prüfen Sie Port 8000: `netstat -ano | findstr :8000`

### Problem 2: "404 Not Found" für `/api/auth/login`

**Ursache:** Falsche Backend-URL

**Lösung:**
1. `.env` Datei prüfen (siehe oben)
2. Frontend-Server neu starten
3. Browser-Cache leeren (Strg+Shift+R)

### Problem 3: "401 Unauthorized" - Falsches Passwort

**Ursache:** Falsche Anmeldedaten oder User existiert nicht

**Lösung:**
- Prüfen Sie die Anmeldedaten
- Standard-Admin-Login:
  - **E-Mail:** admin@schmitz-intralogistik.de
  - **Passwort:** admin123

### Problem 4: "2FA Setup Required"

**Ursache:** User hat noch kein 2FA eingerichtet

**Lösung:**
1. Folgen Sie den Anweisungen auf dem Bildschirm
2. Scannen Sie den QR-Code mit Google Authenticator
3. Geben Sie den 6-stelligen Code ein

### Problem 5: "Invalid 2FA code"

**Ursache:** 2FA-Code ist falsch oder abgelaufen

**Lösung:**
1. Prüfen Sie die Uhrzeit auf Ihrem Gerät
2. Generieren Sie einen neuen Code in Google Authenticator
3. Geben Sie den Code schnell ein (gültig für 30 Sekunden)

## Vollständige Start-Anleitung

### Terminal 1: Backend-Server

```powershell
cd C:\Users\mschm\Stundenzettel_web\backend
.\venv\Scripts\Activate.ps1
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2: Frontend-Server

```powershell
cd C:\Users\mschm\Stundenzettel_web\frontend
npm start
```

### Browser

Öffnen Sie: **http://localhost:3000**

## Test des Backend-Servers

**Prüfen Sie, ob Backend erreichbar ist:**

1. Öffnen Sie: **http://localhost:8000/docs**
2. Sollte die Swagger API-Dokumentation zeigen

**Oder mit PowerShell:**

```powershell
# Test-Request an Backend
curl http://localhost:8000/api/auth/me
# Sollte 401 zurückgeben (nicht erreichbar = kein Response oder Timeout)
```

## MongoDB prüfen

**Falls Backend-Fehler auftreten, prüfen Sie MongoDB:**

```powershell
# MongoDB Service prüfen
Get-Service MongoDB

# Sollte "Running" anzeigen
# Falls nicht:
net start MongoDB
```

## Debug-Modus aktivieren

**Für detaillierte Fehlermeldungen:**

**Backend (.env):**
```env
LOG_LEVEL=DEBUG
```

**Frontend (Browser Console):**
```javascript
// In Browser Console (F12):
localStorage.setItem('debug', 'true');
```

## Checkliste

- [ ] Backend-Server läuft auf Port 8000
- [ ] Frontend-Server läuft auf Port 3000
- [ ] MongoDB Service läuft
- [ ] `.env` Datei in `frontend/` ist korrekt konfiguriert
- [ ] `.env` Datei in `backend/` ist korrekt konfiguriert
- [ ] Browser-Konsole zeigt keine Fehler
- [ ] Netzwerk-Tab zeigt erfolgreiche Requests (Status 200)

## Standard-Anmeldedaten

**Admin-User:**
- E-Mail: `admin@schmitz-intralogistik.de`
- Passwort: `admin123`
- **Wichtig:** Nach erstem Login muss 2FA eingerichtet werden!

## Support

Falls nichts hilft, sammeln Sie folgende Informationen:

1. **Browser-Konsole-Fehler** (F12 → Console)
2. **Netzwerk-Tab-Requests** (F12 → Network → Screenshot)
3. **Backend-Terminal-Ausgabe**
4. **Frontend-Terminal-Ausgabe**

