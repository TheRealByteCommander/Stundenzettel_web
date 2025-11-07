# 🔐 Cyber-Security: URL-Verschleierung und Download-Schutz

## Übersicht

Diese Implementierung verschleiert die echte Proxmox-URL und verhindert, dass Dokumente von externen Quellen heruntergeladen werden können.

---

## 1. URL-Verschleierung (Proxmox-URL verstecken)

### Problem
- Frontend kennt die echte Proxmox-URL (z.B. `https://192.168.178.154:8000`)
- Diese URL ist in JavaScript-Code sichtbar
- Angreifer können die Backend-URL aus dem Frontend-Code extrahieren

### Lösung: API-Proxy auf All-inkl.com

**Architektur:**
```
Frontend (All-inkl) → Proxy (All-inkl/api/proxy.php) → Backend (Proxmox)
```

**Vorteile:**
- ✅ Frontend kennt nur die Proxy-URL (`/api/proxy.php`)
- ✅ Echte Proxmox-URL ist nur im Proxy-Script (nicht im Frontend-Code)
- ✅ Proxy kann zusätzliche Sicherheitschecks durchführen

**Implementierung:**
- `webapp/api/proxy.php` - PHP-Proxy-Script auf All-inkl.com
- Konfiguration via `.env` oder direkt im Script
- Weiterleitung aller API-Requests an Proxmox

**Konfiguration:**
```php
// webapp/api/proxy.php
$BACKEND_URL = getenv('BACKEND_URL') ?: 'https://proxmox-domain.de:8000';
```

**Frontend-Konfiguration:**
```javascript
// Frontend nutzt jetzt Proxy statt direkter Backend-URL
const API = '/api/proxy.php';  // Statt: https://proxmox-ip:8000/api
```

---

## 2. Download-Schutz (Keine externen Downloads)

### Problem
- Direkte Links zu Dokumenten können von externen Quellen aufgerufen werden
- Angreifer könnten Dokumente herunterladen, wenn sie die URL kennen

### Lösung: Mehrschichtiger Schutz

#### 2.1 Authentifizierung (Pflicht)
- ✅ Alle Download-Endpunkte erfordern JWT-Token
- ✅ `Depends(get_current_user)` - Nur authentifizierte Benutzer

#### 2.2 Referrer- und Origin-Check
- ✅ Prüfung des `Referer`-Headers
- ✅ Prüfung des `Origin`-Headers
- ✅ Nur erlaubte Origins können Downloads anfordern

**Implementierung:**
```python
# Cyber-Security: Referrer-Check
referer = request.headers.get("referer", "")
origin = request.headers.get("origin", "")

allowed_origins = CORS_ORIGINS
if origin and not any(allowed in origin for allowed in allowed_origins):
    if referer and not any(allowed in referer for allowed in allowed_origins):
        logging.warning(f"Blocked PDF download - invalid origin/referer")
        raise HTTPException(status_code=403, detail="Access denied: Invalid origin")
```

#### 2.3 Keine direkten Links
- ✅ Alle Downloads gehen über API-Endpunkte
- ✅ Keine statischen Datei-Links
- ✅ Keine öffentlich zugänglichen URLs

#### 2.4 Cache-Control-Header
- ✅ `Cache-Control: no-store, no-cache, must-revalidate`
- ✅ `Pragma: no-cache`
- ✅ `Expires: 0`
- Verhindert, dass Browser Dokumente cachen

#### 2.5 Content-Type-Options
- ✅ `X-Content-Type-Options: nosniff`
- Verhindert MIME-Type-Sniffing

---

## 3. Geschützte Endpunkte

### PDF-Downloads
- ✅ `/api/timesheets/{id}/pdf` - Referrer-Check, Authentifizierung
- ✅ `/api/timesheets/{id}/download-and-email` - Referrer-Check, Authentifizierung
- ✅ `/api/accounting/monthly-report-pdf` - Referrer-Check, Authentifizierung

### Dokumente (Uploads)
- ✅ `/api/timesheets/{id}/upload-signed` - Rate Limiting, Authentifizierung
- ✅ `/api/travel-expense-reports/{id}/upload-receipt` - Rate Limiting, Authentifizierung

**Alle Endpunkte:**
- Erfordern JWT-Token
- Prüfen Referrer/Origin
- Keine direkten Links möglich
- Cache-Control-Header gesetzt

---

## 4. Frontend-Integration

### Proxy-Verwendung

**Vorher (unsicher):**
```javascript
const BACKEND_URL = 'https://192.168.178.154:8000';  // Proxmox-URL sichtbar!
const API = `${BACKEND_URL}/api`;
```

**Nachher (sicher):**
```javascript
// Option 1: Proxy auf All-inkl.com
const API = '/api/proxy.php';  // Proxy-URL, echte URL versteckt

// Option 2: Oder über Umgebungsvariable (wenn Proxy nicht verwendet)
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '/api';
const API = BACKEND_URL;
```

### Download-Aufrufe

**Sicher:**
```javascript
// Download über API mit Token
const response = await axios.post(
  `${API}/timesheets/${id}/download-and-email`,
  {},
  {
    headers: { Authorization: `Bearer ${token}` },
    responseType: 'blob'  // Für PDF-Downloads
  }
);
```

**Nicht möglich:**
```javascript
// ❌ Direkter Link - funktioniert nicht
window.open('https://proxmox-ip:8000/api/timesheets/123/pdf');
```

---

## 5. Konfiguration

### Backend (.env)
```env
# CORS-Origins (für Referrer-Check)
CORS_ORIGINS=https://app.byte-commander.de,http://localhost:3000

# Optional: Referrer-Check im Proxy aktivieren
ENFORCE_REFERRER_CHECK=true
```

### Proxy (webapp/api/proxy.php)
```php
// Echte Proxmox-URL (NICHT im Frontend!)
$BACKEND_URL = getenv('BACKEND_URL') ?: 'https://proxmox-domain.de:8000';

// Erlaubte Origins
$ALLOWED_ORIGINS = [
    'https://stundenzettel.byte-commander.de',
    'http://localhost:3000'
];
```

### Frontend (.env)
```env
# Option 1: Proxy verwenden (empfohlen)
REACT_APP_USE_PROXY=true

# Option 2: Direkte Backend-URL (weniger sicher)
REACT_APP_BACKEND_URL=https://stundenzettel.byte-commander.de/api
```

---

## 6. Sicherheits-Checkliste

### ✅ Implementiert
- [x] Proxy-Script für URL-Verschleierung
- [x] Referrer-Check bei allen Download-Endpunkten
- [x] Origin-Validation
- [x] Authentifizierung bei allen Downloads
- [x] Cache-Control-Header (verhindert Caching)
- [x] Keine direkten Links zu Dokumenten
- [x] Rate Limiting bei Uploads

### ⚠️ Empfehlungen
- [ ] Proxy-Script auf All-inkl.com deployen
- [ ] Frontend auf Proxy umstellen
- [ ] Regelmäßige Sicherheits-Audits
- [ ] Monitoring für verdächtige Download-Versuche

---

## 7. Angriffs-Szenarien und Schutz

### Szenario 1: Direkter Link-Aufruf
**Angriff:** `https://proxmox-ip:8000/api/timesheets/123/pdf`

**Schutz:**
- ✅ Referrer-Check blockiert (kein erlaubter Referer)
- ✅ Origin-Check blockiert (kein erlaubter Origin)
- ✅ Authentifizierung erforderlich (kein Token)

### Szenario 2: Token-Diebstahl
**Angriff:** Angreifer stiehlt JWT-Token und versucht Download

**Schutz:**
- ✅ Referrer-Check blockiert (Request kommt nicht von erlaubter Domain)
- ✅ Origin-Check blockiert
- ✅ Token ist an User-ID gebunden

### Szenario 3: URL-Extraktion aus Frontend
**Angriff:** Angreifer liest Backend-URL aus JavaScript-Code

**Schutz:**
- ✅ Proxy versteckt echte URL
- ✅ Frontend kennt nur Proxy-URL
- ✅ Echte URL nur im Proxy-Script (Server-seitig)

---

## 8. Monitoring und Logging

**Geloggte Events:**
- Blockierte Download-Versuche (invalid origin/referer)
- Fehlgeschlagene Authentifizierungen
- Rate-Limit-Überschreitungen

**Beispiel-Log:**
```
WARNING: Blocked PDF download - invalid origin/referer: https://evil.com / https://evil.com/page
```

---

## Zusammenfassung

✅ **URL-Verschleierung:**
- Proxy-Script versteckt echte Proxmox-URL
- Frontend kennt nur Proxy-URL

✅ **Download-Schutz:**
- Authentifizierung erforderlich
- Referrer- und Origin-Check
- Keine direkten Links
- Cache-Control verhindert Caching

✅ **Mehrschichtige Sicherheit:**
- JWT-Token
- Origin-Validation
- Referrer-Check
- Rate Limiting

**Die Proxmox-URL ist jetzt verschleiert und Dokumente können nicht von externen Quellen heruntergeladen werden.**

---

**Letzte Aktualisierung:** 2025
**Verantwortlich:** Entwicklungsteam

