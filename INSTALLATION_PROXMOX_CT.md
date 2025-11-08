# 🧰 Installation: Tick Guard in zwei Proxmox Containern (Ubuntu 22.04 LXC)

Diese Anleitung beschreibt Schritt für Schritt, wie du das System vollständig lokal in zwei Proxmox-Containern (CT) mit Ubuntu 22.04 (Minimal) installierst und weltweit via DDNS erreichst. Zielbild:

```
Internet → DDNS → CT-Frontend (Nginx + React Build + TLS)
                         ↘︎ interne Bridge (LAN/VPN)
                           CT-Backend (FastAPI + MongoDB + Storage)
                                     ↘︎ GMKTec evo x2 (Ollama, Port 11434)
```

---

## 1. Voraussetzungen

- Proxmox VE 7.x oder 8.x
- Ubuntu 22.04 LXC-Template (unprivileged)
- GMKTec evo x2 im lokalen Netz mit Ollama
- Öffentliche IP + Portweiterleitung (443/tcp) oder Reverse Proxy Upstream
- DynDNS-Account (z. B. `ddns.meinedomain.de`)
- SSH-Keys für den Zugriff auf die Container

---

## 2. Container anlegen

### 2.1 Backend-Container (`ct-backend`)

| Einstellung             | Wert                              |
|-------------------------|-----------------------------------|
| Hostname                | `tick-backend`                    |
| Template                | Ubuntu 22.04                      |
| CPUs                    | 4 vCPU                            |
| RAM                     | 6–8 GB                            |
| Storage                 | 40 GB (SSD), Backup-geeignet      |
| Netzwerk                | Bridge (z. B. `vmbr0`), statische IP im LAN |
| Nesting                 | aktivieren (für Python venv)      |
| Unprivileged            | ✅                                |

### 2.2 Frontend-Container (`ct-frontend`)

| Einstellung             | Wert                              |
|-------------------------|-----------------------------------|
| Hostname                | `tick-frontend`                   |
| Template                | Ubuntu 22.04                      |
| CPUs                    | 2 vCPU                            |
| RAM                     | 2 GB                              |
| Storage                 | 15 GB                             |
| Netzwerk                | Gleiche Bridge, statische IP      |
| Nesting                 | optional                          |
| Unprivileged            | ✅                                |

> **Tipp:** CTs mit `cgroup2` und gelegentlich `keyctl=1` (Features) erstellen, falls `systemd`-Dienste in LXC streiken.

---

## 3. Basis-Konfiguration (beide CTs)

```bash
apt update
apt full-upgrade -y
apt install -y curl wget htop ca-certificates gnupg ufw
timedatectl set-timezone Europe/Berlin
```

### Firewall

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw enable
```

Frontend-CT: später `ufw allow 443/tcp`. Backend-CT: nur lokale IPs z. B. `ufw allow from 192.168.178.0/24 to any port 8000`.

---

## 4. Backend-Container installieren

### 4.1 Pakete & Python

```bash
apt install -y python3.11 python3.11-venv python3-pip git build-essential mongodb
systemctl enable --now mongodb
```

### 4.2 Projekt deployen

```bash
mkdir -p /opt/tick-guard && cd /opt/tick-guard
git clone <REPO_URL> stundenzettel_web
chown -R $USER:$USER stundenzettel_web
cd stundenzettel_web/backend

python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4.3 Dateispeicher

```bash
mkdir -p /var/tick-guard/receipts
chown -R $USER:$USER /var/tick-guard/receipts
```

### 4.4 `.env` erstellen

```bash
cat <<'EOF' > .env
MONGO_URL=mongodb://localhost:27017
DB_NAME=stundenzettel

LOCAL_RECEIPTS_PATH=/var/tick-guard/receipts

SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)

OLLAMA_BASE_URL=http://192.168.178.50:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=300
OLLAMA_MAX_RETRIES=3

CORS_ORIGINS=https://ddns.meinedomain.de,http://localhost:3000
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
VAPID_CLAIM_EMAIL=admin@meinedomain.de
EOF
```

> IP von GMKTec (`OLLAMA_BASE_URL`) anpassen! VAPID-Keys nach Bedarf generieren.

### 4.5 Systemuser & Rechte

```bash
useradd --system --home /opt/tick-guard --shell /usr/sbin/nologin tickguard
chown -R tickguard:tickguard /opt/tick-guard /var/tick-guard
```

### 4.6 Systemd-Service

```ini
# /etc/systemd/system/tick-guard-backend.service
[Unit]
Description=Tick Guard Backend
After=network-online.target mongod.service

[Service]
User=tickguard
Group=tickguard
WorkingDirectory=/opt/tick-guard/stundenzettel_web/backend
Environment="PATH=/opt/tick-guard/stundenzettel_web/backend/venv/bin"
EnvironmentFile=/opt/tick-guard/stundenzettel_web/backend/.env
ExecStart=/opt/tick-guard/stundenzettel_web/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8000
Restart=on-failure
TimeoutStopSec=10

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now tick-guard-backend
curl http://localhost:8000/health
```

---

## 5. Frontend-Container installieren

### 5.1 Pakete

```bash
apt install -y nginx nodejs npm git certbot python3-certbot-nginx
```

### 5.2 Projekt holen & Build

```bash
mkdir -p /opt/tick-guard && cd /opt/tick-guard
git clone <REPO_URL> stundenzettel_web
cd stundenzettel_web/frontend
npm install
cat <<'EOF' > .env.production
REACT_APP_BACKEND_URL=https://ddns.meinedomain.de
EOF
npm run build
```

### 5.3 Build deployen

```bash
rm -rf /var/www/tick-guard
mkdir -p /var/www/tick-guard
cp -r build/* /var/www/tick-guard/
chown -R www-data:www-data /var/www/tick-guard
```

### 5.4 Nginx konfigurieren

```nginx
# /etc/nginx/sites-available/tick-guard
server {
    listen 80;
    server_name ddns.meinedomain.de;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ddns.meinedomain.de;

    ssl_certificate     /etc/letsencrypt/live/ddns.meinedomain.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ddns.meinedomain.de/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;

    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header Referrer-Policy no-referrer;

    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    root /var/www/tick-guard;
    index index.html;

    location /api/ {
        proxy_pass http://192.168.178.154:8000/api/; # Backend-Container-IP
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

```bash
ln -s /etc/nginx/sites-available/tick-guard /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

### 5.5 Zertifikate holen

```bash
certbot --nginx -d ddns.meinedomain.de
systemctl reload nginx
```

> Falls kein Port 80 offen ist (nur VPN), stattdessen DNS-01 oder eigene CA verwenden.

---

## 6. Netzwerk & Sicherheit

1. **Router**: Port 443 → Frontend-CT (oder per DMZ/Reverse Proxy).
2. **WireGuard**: Für Admin/SFTP/SSH Zugänge einrichten (optional).
3. **GMKTec Firewall**: `ufw allow from <Backend-IP> to any port 11434 proto tcp`.
4. **Fail2ban/CrowdSec** auf Frontend-CT aktivieren (`jail.local` für Nginx).
5. **Backups**:
   - `mongodump` per Systemd-Timer oder Cron.
   - `/var/tick-guard/receipts` mit `rsync` auf externes Storage sichern.
   - Konfigurationsdateien (`.env`, Nginx, Systemd) versionieren.

---

## 7. Tests

- `curl -k https://ddns.meinedomain.de/api/health`
- Login als Admin (`admin@schmitz-intralogistik.de` / `admin123`, Passwort direkt ändern).
- Stundenzettel anlegen, PDF generieren, Upload testen.
- Reisekosten-Report prüfen → Agentenworkflow → Ollama-Reaktion kontrollieren.
- Push-Benachrichtigungen und SMTP (falls konfiguriert) testen.

---

## 8. Betrieb & Wartung

- `systemctl status tick-guard-backend` und `journalctl -u tick-guard-backend`.
- `journalctl -u nginx` / `journalctl -u fail2ban`.
- Regelmäßige Security-Updates (`unattended-upgrades` aktivieren).
- Logs rotieren (`logrotate`), Monitoring mit Grafana/Prometheus optional.
- Plausibilitätsprüfungen der DDNS-Aktualisierung (Script/Router).

---

## 9. Fehlerbehebung (Kurz)

| Problem                               | Prüfen                                               |
|---------------------------------------|------------------------------------------------------|
| Frontend 502/504                      | Nginx-Logs (`/var/log/nginx/error.log`), Backend up? |
| Backend 500                           | `journalctl -u tick-guard-backend`                   |
| Ollama nicht erreichbar               | `curl http://192.168.178.50:11434/api/tags`          |
| Zertifikat schlägt fehl               | Port 80 offen? DNS korrekt? Certbot-Logs prüfen      |
| Downloads blockiert                   | `CORS_ORIGINS` / Referrer-Checks / JWT-Erneuerung    |

---

Mit diesen Schritten läuft Tick Guard vollständig im lokalen Proxmox-Netzwerk und ist dennoch weltweit via DDNS erreichbar. Frontend und Backend bleiben getrennt, Sicherheitsmaßnahmen (TLS, Firewalls, Rate-Limiting, Auth) sind zentral umgesetzt.

