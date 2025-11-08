# 🔐 Cyber-Security: Reverse Proxy & Download-Schutz

## Überblick

Das System wird weltweit über einen einzigen Host (`https://<dein-ddns>`) bereitgestellt. Das Frontend-Gateway übernimmt TLS, DDNS und URL-Verschleierung, während das Backend nur intern erreichbar bleibt. Dieses Dokument bündelt die wichtigsten Maßnahmen, um die Infrastruktur abzusichern.

---

## 1. Backend-URL verbergen (Reverse Proxy)

### Architektur
```
Internet → DDNS → Frontend-Gateway (Nginx/Caddy) → Backend-Container (http://backend:8000)
```

- Der Frontend-Container liefert den React-Build **und** fungiert als Reverse Proxy.
- API-Aufrufe laufen über denselben Origin (`https://<ddns>/api/...`); das Backend bleibt im LAN.
- Keine internen IP-Adressen oder Ports sind im Frontend-Bundle sichtbar.

### Nginx-Beispiel
```nginx
server {
    listen 443 ssl http2;
    server_name ddns.meinedomain.de;

    ssl_certificate     /etc/letsencrypt/live/ddns.meinedomain.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ddns.meinedomain.de/privkey.pem;

    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header Referrer-Policy no-referrer;

    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    root /var/www/tick-guard;
    index index.html;

    location /api/ {
        proxy_pass http://backend-container:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        limit_req zone=api burst=20 nodelay;
    }

    location / {
        try_files $uri /index.html;
    }
}
```

### Vorteile
- Frontend-Code enthält keine internen Ziele.
- Sämtliche CORS-Anfragen kommen vom gleichen Origin, Konfiguration bleibt minimal.
- Rate-Limiting, Logging, Fail2ban/CrowdSec oder WAF-Regeln lassen sich zentral steuern.

---

## 2. Download-Schutz

### Backend-Maßnahmen
- Jeder Download-Endpunkt verlangt ein gültiges JWT (`Depends(get_current_user)`).
- Referrer- **und** Origin-Prüfungen validieren die Anfrage gegen `CORS_ORIGINS`.
- Responses setzen Cache- und Sicherheitsheader:
  - `Cache-Control: no-store, no-cache, must-revalidate`
  - `Pragma: no-cache`
  - `Expires: 0`
  - `X-Content-Type-Options: nosniff`

```python
referer = request.headers.get("referer", "")
origin = request.headers.get("origin", "")

allowed = set(CORS_ORIGINS)
if origin and origin not in allowed:
    if referer and referer not in allowed:
        logger.warning("Blocked download – invalid origin/referrer")
        raise HTTPException(status_code=403, detail="Invalid origin")
```

### Frontend-Pattern
```javascript
const API = '/api';
const token = getSecureToken();

const response = await axios.post(
  `${API}/timesheets/${id}/download-and-email`,
  {},
  {
    headers: { Authorization: `Bearer ${token}` },
    responseType: 'blob',
  }
);
```

- Keine öffentlichen Direktlinks – Downloads erfolgen ausschließlich über authentifizierte API-Aufrufe.
- Service Worker und Browser dürfen PDFs nicht persistent cachen.

---

## 3. Konfiguration

### Backend `.env`
```env
CORS_ORIGINS=https://ddns.meinedomain.de,http://localhost:3000
ENFORCE_REFERRER_CHECK=true
```

### Frontend `.env.production`
```env
REACT_APP_BACKEND_URL=https://ddns.meinedomain.de
```

### Firewall & Netzwerk
- Router: Port 443 → Frontend-Container (ggf. Port 80 temporär für ACME-HTTP-01).
- `ufw`/Proxmox-Firewall: Nur 443 von außen erlauben; interne Regeln für 8000/27017/11434 setzen.
- GMKTec: Nur Backend-IP (bzw. WireGuard-Subnetz) für Port 11434 freigeben.

---

## 4. Sicherheits-Checkliste

- [x] TLS & HSTS aktiv.
- [x] Reverse Proxy entfernt interne IP aus dem Frontend.
- [x] Rate-Limiting (`limit_req`) konfiguriert.
- [x] JWT-Auth plus Referrer-/Origin-Check bei allen Downloads.
- [x] Keine direkten Dateilinks; nur geschützte API-Endpunkte.
- [x] CORS beschränkt auf DDNS-Domain + lokale Entwicklungs-Hosts.
- [x] Fail2ban/CrowdSec überwacht Nginx oder Systemd-Logs.
- [x] WireGuard für SSH/Administrationszugriffe.
- [x] Regelmäßige Backups (`mongodump`, Receipt-Verzeichnis, Konfigurationsdateien).

---

## 5. FAQ

**Warum kein separates PHP-Proxy-Script mehr?**  
Das Frontend-Gateway übernimmt Reverse-Proxy, TLS und Sicherheitslogik. Zusätzliche PHP-Ebenen würden die Angriffsfläche erhöhen und sind überflüssig.

**Kann ich mehrere Domains verwenden?**  
Ja. Trage alle Domains/Aliase in `CORS_ORIGINS` ein und erweitere die Nginx/Caddy-Konfiguration entsprechend.

**Wie verhindere ich IP-Leaks bei Fehlermeldungen?**  
Nutze `proxy_intercept_errors on;` und statische Fehlerseiten. Im Backend nur interne Logs, keine detaillierten Fehler an den Client.

---

Mit diesem Setup bleibt die Infrastruktur hinter dem DDNS-Endpunkt verborgen, während Authentifizierung, Rate Limits, Header und CORS zentral im Frontend-Gateway und im Backend durchgesetzt werden.

