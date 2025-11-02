# 🔐 Login-Problem beheben - Schritt für Schritt

## Problem: Login funktioniert nicht

### Schnell-Diagnose

**1. Prüfen Sie, ob Backend läuft:**

```powershell
netstat -ano | findstr :8000
```

**Sollte eine Ausgabe zeigen!** Falls nicht → Backend starten (siehe unten).

**2. Prüfen Sie Browser-Konsole (F12):**

1. Öffnen Sie http://localhost:3000
2. Drücken Sie **F12**
3. Tab **Console** öffnen
4. Versuchen Sie sich einzuloggen
5. **Notieren Sie die Fehlermeldung!**

## Lösung Schritt für Schritt

### Schritt 1: Backend-Server starten (falls nicht läuft)

**Neues PowerShell-Fenster öffnen:**

```powershell
# Navigieren zum Backend-Verzeichnis
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
INFO:     Admin user created: admin@schmitz-intralogistik.de / admin123
```

**Wichtig:** Lassen Sie dieses Terminal-Fenster offen!

### Schritt 2: Frontend .env Datei prüfen

**Prüfen Sie die `.env` Datei:**

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

**WICHTIG:** Frontend-Server nach Änderung neu starten!

### Schritt 3: Frontend-Server neu starten

**Stoppen Sie den Frontend-Server (Strg+C) und starten Sie neu:**

```powershell
cd C:\Users\mschm\Stundenzettel_web\frontend
npm start
```

### Schritt 4: Login versuchen

**Standard-Anmeldedaten:**
- **E-Mail:** `admin@schmitz-intralogistik.de`
- **Passwort:** `admin123`

**Nach dem Login:**
1. **2FA Setup** wird angezeigt (erste Anmeldung)
2. Scannen Sie den QR-Code mit **Google Authenticator**
3. Geben Sie den 6-stelligen Code ein

## Häufige Fehler und Lösungen

### Fehler 1: "Network Error" oder "ERR_CONNECTION_REFUSED"

**Problem:** Backend-Server läuft nicht

**Lösung:**
1. Backend-Server starten (Schritt 1)
2. Prüfen: `netstat -ano | findstr :8000` sollte eine Ausgabe zeigen

### Fehler 2: "404 Not Found" für `/api/auth/login`

**Problem:** Falsche Backend-URL oder Backend läuft auf anderem Port

**Lösung:**
1. Prüfen Sie Backend-Terminal - welcher Port wird angezeigt?
2. `.env` Datei anpassen:
   ```env
   REACT_APP_BACKEND_URL=http://localhost:8000
   ```
3. Frontend-Server neu starten
4. Browser-Cache leeren (Strg+Shift+R)

### Fehler 3: "401 Unauthorized" - "Incorrect email or password"

**Problem:** User existiert nicht oder falsches Passwort

**Lösung:**
1. Prüfen Sie Backend-Terminal - wurde Admin-User erstellt?
2. Sollte zeigen: `Admin user created: admin@schmitz-intralogistik.de / admin123`
3. Falls nicht, Backend-Server neu starten
4. Verwenden Sie exakt:
   - E-Mail: `admin@schmitz-intralogistik.de`
   - Passwort: `admin123`

### Fehler 4: "2FA Setup Required" - Kein QR-Code sichtbar

**Problem:** QR-Code wird nicht angezeigt

**Lösung:**
1. Browser-Console prüfen (F12 → Console)
2. Prüfen Sie Backend-Terminal auf Fehler
3. Stellen Sie sicher, dass Backend erreichbar ist: http://localhost:8000/docs

### Fehler 5: "Invalid 2FA code"

**Problem:** Falscher oder abgelaufener 2FA-Code

**Lösung:**
1. Prüfen Sie die Uhrzeit auf Ihrem Gerät (sollte synchronisiert sein)
2. Generieren Sie einen **neuen** Code in Google Authenticator
3. Geben Sie den Code **schnell** ein (gültig für 30 Sekunden)

### Fehler 6: Browser zeigt keine Fehler, aber Login funktioniert nicht

**Problem:** JavaScript-Fehler oder CORS-Problem

**Lösung:**
1. Browser-Console öffnen (F12 → Console)
2. Alle roten Fehlermeldungen notieren
3. Network-Tab prüfen (F12 → Network):
   - Request zu `/api/auth/login` sollte **200** Status haben
   - Falls **CORS error**: Backend-Server neu starten

## Backend API testen

**Testen Sie, ob Backend erreichbar ist:**

1. Öffnen Sie: **http://localhost:8000/docs**
   - Sollte die Swagger API-Dokumentation zeigen

2. **Oder mit PowerShell:**
   ```powershell
   # Test-Request
   curl http://localhost:8000/api/auth/me
   # Sollte 401 zurückgeben (nicht erreichbar = kein Response)
   ```

## MongoDB prüfen

**Falls Backend-Fehler auftreten:**

```powershell
# MongoDB Service prüfen
Get-Service MongoDB

# Sollte "Running" anzeigen
# Falls nicht:
net start MongoDB
```

## Vollständige Checkliste

- [ ] MongoDB Service läuft (`Get-Service MongoDB`)
- [ ] Backend-Server läuft auf Port 8000 (`netstat -ano | findstr :8000`)
- [ ] Frontend-Server läuft auf Port 3000 (`netstat -ano | findstr :3000`)
- [ ] `.env` Datei in `frontend/` ist korrekt: `REACT_APP_BACKEND_URL=http://localhost:8000`
- [ ] Backend-Terminal zeigt: `Admin user created: admin@schmitz-intralogistik.de / admin123`
- [ ] Browser-Konsole zeigt keine Fehler (F12 → Console)
- [ ] Network-Tab zeigt erfolgreiche Requests (Status 200 für `/api/auth/login`)

## Standard-Anmeldedaten

**Erste Anmeldung:**
- E-Mail: `admin@schmitz-intralogistik.de`
- Passwort: `admin123`
- **Nach Login:** 2FA einrichten (obligatorisch)

## Debug-Modus

**Für detaillierte Fehlermeldungen im Backend:**

Backend `.env` hinzufügen:
```env
DEBUG=True
LOG_LEVEL=DEBUG
```

Dann Backend-Server neu starten.

## Wenn nichts funktioniert

**Sammeln Sie folgende Informationen:**

1. **Backend-Terminal-Ausgabe** (komplett kopieren)
2. **Frontend-Terminal-Ausgabe** (komplett kopieren)
3. **Browser-Console** (F12 → Console → Screenshot)
4. **Network-Tab** (F12 → Network → Screenshot)

Dann können wir das Problem gezielt beheben.

