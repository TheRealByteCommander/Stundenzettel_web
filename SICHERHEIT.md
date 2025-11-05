# 🔒 Sicherheitsrichtlinien und Implementierung

## Übersicht

Dieses Dokument beschreibt die Sicherheitsmaßnahmen für die Stundenzettel-Web-Anwendung, einschließlich Datenverschlüsselung, Übertragungssicherheit und Zugriffskontrolle.

---

## 1. Datenübertragung (Transport Layer Security)

### HTTPS/TLS

**Status:** ✅ Implementiert

**Implementierung:**
- **Backend:** HTTPS-Erzwingung via Middleware (konfigurierbar via `ENFORCE_HTTPS=true`)
- **Frontend:** Nutzt HTTPS für alle API-Aufrufe
- **Nginx Reverse Proxy:** SSL/TLS-Terminierung mit Let's Encrypt-Zertifikaten

**Konfiguration:**
```env
# backend/.env
ENFORCE_HTTPS=true  # Nur in Produktion aktivieren
```

**Nginx SSL-Konfiguration:**
```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;
```

**HSTS (HTTP Strict Transport Security):**
- Automatisch aktiviert, wenn HTTPS erkannt wird
- `max-age=31536000; includeSubDomains; preload`

### CORS (Cross-Origin Resource Sharing)

**Status:** ✅ Konfiguriert und restriktiv

**Implementierung:**
- Nur explizit erlaubte Origins aus `.env`
- Keine Credentials über CORS
- Explizite Methoden und Headers (nicht `*`)

**Konfiguration:**
```env
# backend/.env
CORS_ORIGINS=https://stundenzettel.byte-commander.de,http://localhost:3000
```

**Middleware:**
```python
allow_credentials=False  # Keine Credentials über CORS
allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]  # Explizit
allow_headers=["Content-Type", "Authorization"]  # Explizit
max_age=3600  # Preflight-Cache: 1 Stunde
```

---

## 2. Datenverschlüsselung (Storage)

### Dokumente (PDFs)

**Status:** ✅ Implementiert (DSGVO-konform)

**Implementierung:**
- Alle hochgeladenen PDFs werden automatisch verschlüsselt
- Verwendet `Fernet` (symmetric encryption) aus `cryptography`
- Schlüssel aus Umgebungsvariable `ENCRYPTION_KEY`

**Speicherung:**
- Lokal auf Proxmox-Server (nicht auf Webserver)
- Verschlüsselt in strukturierten Ordnern:
  - `LOCAL_RECEIPTS_PATH/reisekosten/User_Monat_ReportID/`
  - `LOCAL_RECEIPTS_PATH/stundenzettel/User_Woche_TimesheetID/`

**Konfiguration:**
```env
# backend/.env
ENCRYPTION_KEY=your-44-character-base64-encoded-key
LOCAL_RECEIPTS_PATH=/var/stundenzettel/receipts
```

**Schlüssel-Generierung:**
```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # In .env eintragen
```

### Passwörter

**Status:** ✅ Bcrypt-Hashing

**Implementierung:**
- Passwörter werden mit `bcrypt` gehasht (Salt automatisch)
- Mindestens 8 Zeichen erforderlich
- Maximal 128 Zeichen

### Sensible Daten in MongoDB

**Status:** ⚠️ Teilweise verschlüsselt

**Implementierung:**
- Passwörter: Gehasht (bcrypt)
- 2FA-Secrets: Klartext (aber nur für Authentifizierung)
- E-Mail-Adressen: Klartext (für Login erforderlich)

**Empfehlung:**
- MongoDB sollte mit TLS verbunden werden
- Sensible Felder können zusätzlich verschlüsselt werden

---

## 3. Authentifizierung und Autorisierung

### JWT (JSON Web Tokens)

**Status:** ✅ Implementiert

**Implementierung:**
- Token-basierte Authentifizierung
- Ablaufzeit: 24 Stunden (konfigurierbar)
- Secret-Key aus Umgebungsvariable

**Konfiguration:**
```env
# backend/.env
SECRET_KEY=your-secret-key-min-32-characters
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 Stunden
```

**Token-Validierung:**
- Jeder API-Request erfordert gültigen Token
- Token in `Authorization: Bearer <token>` Header

### 2FA (Two-Factor Authentication)

**Status:** ✅ Obligatorisch

**Implementierung:**
- TOTP (Time-based One-Time Password) via `pyotp`
- QR-Code für Setup
- Obligatorisch für alle Benutzer

**Speicherung:**
- Secret in MongoDB (User-Dokument)
- Nur für Authentifizierung verwendet

### Rollenbasierte Zugriffskontrolle (RBAC)

**Status:** ✅ Implementiert

**Rollen:**
- `user`: Standard-Benutzer
- `accounting`: Buchhaltung (kann Reisekosten genehmigen)
- `admin`: Administrator (voller Zugriff)

**Implementierung:**
- Rollenprüfung in jedem Endpunkt
- `can_view_all_data()` für Admin/Accounting
- `get_admin_user()` / `get_accounting_or_admin_user()` Dependencies

---

## 4. Rate Limiting

**Status:** ✅ Implementiert

**Implementierung:**
- `slowapi` für Rate Limiting
- IP-basiert (get_remote_address)

**Limits:**
- Login: 5 Versuche pro Minute
- Registrierung: 3 pro Stunde
- Upload unterschriebener Stundenzettel: 10 pro Stunde
- Upload Reisekosten-Belege: 20 pro Stunde

**Konfiguration:**
```python
@limiter.limit("5/minute")
@api_router.post("/auth/login")
```

---

## 5. Security Headers

**Status:** ✅ Implementiert

**Header:**
- `X-Content-Type-Options: nosniff` - Verhindert MIME-Type-Sniffing
- `X-Frame-Options: DENY` - Verhindert Clickjacking
- `X-XSS-Protection: 1; mode=block` - XSS-Schutz (Browser)
- `Referrer-Policy: strict-origin-when-cross-origin` - Referrer-Kontrolle
- `Permissions-Policy: geolocation=(), microphone=(), camera=()` - Feature-Policy
- `Content-Security-Policy` - CSP (siehe unten)
- `Strict-Transport-Security` - HSTS (nur bei HTTPS)

**Content Security Policy (CSP):**
```
default-src 'self';
script-src 'self' 'unsafe-inline' 'unsafe-eval';
style-src 'self' 'unsafe-inline';
img-src 'self' data: https:;
font-src 'self' data:;
connect-src 'self' https:;
frame-ancestors 'none';
```

**Hinweis:** `unsafe-inline` und `unsafe-eval` sollten in Produktion entfernt werden, wenn möglich.

---

## 6. Input Validation

**Status:** ✅ Implementiert

**Backend:**
- Pydantic-Modelle für alle API-Inputs
- Type-Validation automatisch
- Email-Validation via `email-validator`

**Frontend:**
- `sanitizeHTML()` - XSS-Schutz
- `sanitizeInput()` - Gefährliche Zeichen entfernen
- `validateEmail()` - E-Mail-Format-Prüfung
- `validatePassword()` - Passwort-Stärke
- `validateFilename()` - Path-Traversal-Schutz

**Beispiele:**
```javascript
// Frontend
sanitizeInput(userInput);
escapeHTML(displayText);

// Backend
class UserCreate(BaseModel):
    email: EmailStr  # Automatische Validierung
    password: str = Field(min_length=8, max_length=128)
```

---

## 7. Audit-Logging

**Status:** ✅ Implementiert (DSGVO-konform)

**Implementierung:**
- Alle Zugriffe auf sensible Daten werden protokolliert
- Speicherung in MongoDB (Collection: `audit_logs`)
- Logs enthalten: User, Aktion, Ressource, Zeitstempel

**Beispiele:**
- Upload von Dokumenten
- Genehmigung von Reisekosten
- Zugriff auf Benutzerdaten

**Konfiguration:**
```python
audit_logger.log_access(
    action="upload",
    user_id=user_id,
    resource_type="receipt",
    resource_id=receipt_id,
    details={...}
)
```

---

## 8. DSGVO-Compliance

**Status:** ✅ Implementiert

**Features:**
- **Verschlüsselung:** Automatische Verschlüsselung aller PDFs
- **Audit-Logging:** Alle Zugriffe protokolliert
- **Retention-Management:** Automatische Löschung nach Aufbewahrungsfrist
- **Lokale Speicherung:** Dokumente nur auf Proxmox (nicht All-inkl)

**Aufbewahrungsfristen:**
- Reisekostenbelege: 10 Jahre (GoBD)
- Genehmigte Abrechnungen: 10 Jahre
- Entwürfe: 1 Jahr

---

## 9. Frontend-Sicherheit

**Status:** ✅ Implementiert

**Token-Speicherung:**
- Secure Token Storage (nicht localStorage)
- Automatische Token-Erneuerung
- Token bei Logout gelöscht

**XSS-Schutz:**
- DOMPurify für HTML-Sanitization
- Input-Sanitization vor Anzeige
- React-Escape automatisch

**CSRF-Schutz:**
- Token-basierte Authentifizierung
- SameSite-Cookies (wenn verwendet)

---

## 10. Checkliste für Produktion

### Backend (.env)
- [ ] `SECRET_KEY` gesetzt (min. 32 Zeichen, zufällig)
- [ ] `ENCRYPTION_KEY` gesetzt (44 Zeichen, base64)
- [ ] `ENFORCE_HTTPS=true` (nur in Produktion)
- [ ] `CORS_ORIGINS` auf Produktions-URLs beschränkt
- [ ] `MONGO_URL` mit Authentifizierung (nicht `localhost` ohne Auth)
- [ ] `VAPID_PUBLIC_KEY` und `VAPID_PRIVATE_KEY` gesetzt

### Server-Konfiguration
- [ ] HTTPS/SSL-Zertifikat installiert (Let's Encrypt)
- [ ] Nginx Reverse Proxy konfiguriert
- [ ] Firewall-Regeln: Nur notwendige Ports offen
- [ ] MongoDB TLS aktiviert
- [ ] Regelmäßige Backups

### Code
- [ ] CSP angepasst (unsafe-inline/eval entfernen wenn möglich)
- [ ] Rate Limiting aktiviert
- [ ] Security Headers aktiv
- [ ] Audit-Logging aktiv

### Monitoring
- [ ] Logs überwachen (Fehlgeschlagene Logins, Rate Limits)
- [ ] Alerts für verdächtige Aktivitäten
- [ ] Regelmäßige Sicherheits-Updates

---

## 11. Bekannte Sicherheitsüberlegungen

### MongoDB-Authentifizierung
- MongoDB sollte mit Benutzername/Passwort konfiguriert werden
- TLS-Verbindung empfohlen

### CSP (Content Security Policy)
- Aktuell: `unsafe-inline` und `unsafe-eval` aktiv
- **Empfehlung:** In Produktion entfernen, wenn möglich
- React benötigt möglicherweise `unsafe-inline` für Styles

### 2FA-Secrets
- Aktuell: Klartext in MongoDB
- **Empfehlung:** Optional verschlüsselt speichern

### Token-Rotation
- Aktuell: Token gültig für 24 Stunden
- **Empfehlung:** Refresh-Token-Mechanismus implementieren

---

## 12. Sicherheits-Updates

**Regelmäßige Wartung:**
- Dependencies aktualisieren (`pip list --outdated`)
- Sicherheits-Patches einspielen
- Logs überprüfen
- Penetration-Testing (optional)

**Resources:**
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Mozilla Security Guidelines](https://infosec.mozilla.org/guidelines/web_security)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

---

## Zusammenfassung

✅ **Implementiert:**
- HTTPS/TLS für Übertragung
- Verschlüsselung aller Dokumente
- JWT-basierte Authentifizierung
- Obligatorische 2FA
- Rate Limiting
- Security Headers
- Input Validation
- Audit-Logging
- DSGVO-Compliance

⚠️ **Empfehlungen:**
- CSP verschärfen (unsafe-inline/eval entfernen)
- MongoDB TLS aktivieren
- 2FA-Secrets optional verschlüsseln
- Refresh-Token-Mechanismus

---

**Letzte Aktualisierung:** 2024
**Verantwortlich:** Entwicklungsteam

