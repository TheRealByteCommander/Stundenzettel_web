# 🧰 Installation: Tick Guard in zwei Proxmox Containern (Ubuntu 22.04 LXC)

Diese Anleitung beschreibt Schritt für Schritt, wie du das System vollständig lokal in zwei Proxmox-Containern (CT) mit Ubuntu 22.04 (Minimal) installierst und weltweit via DDNS erreichst. Zielbild:

```
Internet → DDNS → CT-Frontend 192.168.178.150 (Nginx + React Build + TLS)
                         ↘︎ interne Bridge (LAN/VPN)
                           CT-Backend 192.168.178.151 (FastAPI + MongoDB + Storage)
                                     ↘︎ GMKTec evo x2 192.168.178.155 (Ollama, Port 11434)
```

---

## 1. Voraussetzungen

- Proxmox VE 7.x oder 8.x
- Ubuntu 22.04 LXC-Template (unprivileged)
- GMKTec evo x2 im lokalen Netz mit Ollama
- Öffentliche IP + Portweiterleitung (443/tcp) oder Reverse Proxy Upstream
- DynDNS-Account (z. B. `ddns.meinedomain.de`)
- SSH-Keys für den Zugriff auf die Container

**Referenz-IP-Plan**

| Rolle                | Hostname        | IP-Adresse       |
|----------------------|-----------------|------------------|
| Frontend-CT          | `tick-frontend` | `192.168.178.150` |
| Backend-CT           | `tick-backend`  | `192.168.178.151` |
| GMKTec evo x2/Ollama | `gmktec`        | `192.168.178.155` |

> Verwende identische IPs oder passe die folgenden Befehle entsprechend an.

---

## 2. Automatisierte Installation (Empfohlen)

Die Skripte aus dem Repository automatisieren sämtliche Schritte (Pakete, Konfiguration, Dienste). Sie können direkt auf den jeweiligen Containern ausgeführt werden. Bei Bedarf Variablen wie `DDNS_DOMAIN`, `FRONTEND_IP`, `BACKEND_IP`, `OLLAMA_IP`, `CORS_ORIGINS`, `CERTBOT_EMAIL` anpassen.

**Backend-Container (`192.168.178.151`)**

```bash
curl -fsSL https://raw.githubusercontent.com/TheRealByteCommander/Stundenzettel_web/main/scripts/install_backend_ct.sh \
 | sudo DDNS_DOMAIN=my.ddns.example FRONTEND_IP=192.168.178.150 BACKEND_IP=192.168.178.151 \
   OLLAMA_IP=192.168.178.155 LOCAL_RECEIPTS_PATH=/var/tick-guard/receipts bash
```

**Frontend-Container (`192.168.178.150`)**

```bash
curl -fsSL https://raw.githubusercontent.com/TheRealByteCommander/Stundenzettel_web/main/scripts/install_frontend_ct.sh \
 | sudo DDNS_DOMAIN=my.ddns.example BACKEND_HOST=192.168.178.151 BACKEND_PORT=8000 bash
```

Für die automatische Ausstellung eines TLS-Zertifikats via Let’s Encrypt:

```bash
curl -fsSL https://raw.githubusercontent.com/TheRealByteCommander/Stundenzettel_web/main/scripts/install_frontend_ct.sh \
 | sudo DDNS_DOMAIN=my.ddns.example BACKEND_HOST=192.168.178.151 BACKEND_PORT=8000 \
   RUN_CERTBOT=true CERTBOT_EMAIL=admin@my.ddns.example bash
```

Die folgenden Abschnitte beschreiben die manuellen Schritte im Detail und dienen als Referenz, falls einzelne Komponenten individuell angepasst werden sollen.

---

## 3. Container anlegen

### 2.1 Backend-Container (`ct-backend`)

| Einstellung             | Wert                              |
|-------------------------|-----------------------------------|
| Hostname                | `tick-backend`                    |
| Template                | Ubuntu 22.04                      |
| CPUs                    | 4 vCPU                            |
| RAM                     | 6–8 GB                            |
| Storage                 | 40 GB (SSD), Backup-geeignet      |
| Netzwerk                | Bridge (z. B. `vmbr0`), statische IP `192.168.178.151/24` |
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
| Netzwerk                | Gleiche Bridge, statische IP `192.168.178.150/24` |
| Nesting                 | optional                          |
| Unprivileged            | ✅                                |

> **Tipp:** CTs mit `cgroup2` und gelegentlich `keyctl=1` (Features) erstellen, falls `systemd`-Dienste in LXC streiken.

---

## 4. Basis-Konfiguration (beide CTs)

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

Frontend-CT: später `ufw allow 443/tcp`. Backend-CT: nur Frontend-IP zulassen, z. B. `ufw allow from 192.168.178.150 to any port 8000 proto tcp`.

---

## 5. Backend-Container installieren

### 4.1 Pakete & Python

```bash
apt install -y python3 python3-venv python3-pip git build-essential mongodb
systemctl enable --now mongodb
```

### 4.2 Projekt deployen

```bash
mkdir -p /opt/tick-guard && cd /opt/tick-guard
git clone <REPO_URL> stundenzettel_web
chown -R $USER:$USER stundenzettel_web
cd stundenzettel_web/backend

python3 -m venv venv
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

OLLAMA_BASE_URL=http://192.168.178.155:11434
OLLAMA_MODEL=llama3.2
OLLAMA_MODEL_CHAT=llama3.2
OLLAMA_MODEL_DOCUMENT=mistral-nemo
OLLAMA_MODEL_ACCOUNTING=llama3.1
OLLAMA_TIMEOUT=300
OLLAMA_MAX_RETRIES=3

CORS_ORIGINS=https://ddns.meinedomain.de,http://localhost:3000
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
VAPID_CLAIM_EMAIL=admin@meinedomain.de
EOF
```

> IPs verwenden: Frontend `192.168.178.150`, Backend `192.168.178.151`, GMKTec `192.168.178.155`. VAPID-Keys nach Bedarf generieren.

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
systemctl status tick-guard-backend --no-pager
sudo -u tickguard /opt/tick-guard/stundenzettel_web/backend/venv/bin/uvicorn --version
curl http://localhost:8000/health
```

---

## 6. Frontend-Container installieren

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
        proxy_pass http://192.168.178.151:8000/api/; # Backend-Container-IP
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

## 7. Netzwerk & Sicherheit

1. **Router**: Port 443 → Frontend-CT `192.168.178.150` (oder per vorgelagertem Proxy).
2. **WireGuard**: Für Admin/SFTP/SSH Zugänge einrichten (optional).
3. **GMKTec Firewall**: `ufw allow from 192.168.178.151 to any port 11434 proto tcp`.
4. **Fail2ban/CrowdSec** auf Frontend-CT aktivieren (`jail.local` für Nginx).
5. **Backups**:
   - `mongodump` per Systemd-Timer oder Cron.
   - `/var/tick-guard/receipts` mit `rsync` auf externes Storage sichern.
   - Konfigurationsdateien (`.env`, Nginx, Systemd) versionieren.

---

## 8. Tests

- `curl -k https://ddns.meinedomain.de/api/health`
- Login als Admin (`admin@schmitz-intralogistik.de` / `admin123`, Passwort direkt ändern).
- Stundenzettel anlegen, PDF generieren, Upload testen.
- Reisekosten-Report prüfen → Agentenworkflow → Ollama-Reaktion kontrollieren.
- Push-Benachrichtigungen und SMTP (falls konfiguriert) testen.

---

## 9. Betrieb & Wartung

- `systemctl status tick-guard-backend` und `journalctl -u tick-guard-backend`.
- `journalctl -u nginx` / `journalctl -u fail2ban`.
- Regelmäßige Security-Updates (`unattended-upgrades` aktivieren).
- Logs rotieren (`logrotate`), Monitoring mit Grafana/Prometheus optional.
- Plausibilitätsprüfungen der DDNS-Aktualisierung (Script/Router).

---

## 10. Fehlerbehebung (Kurz)

| Problem                               | Prüfen                                               |
|---------------------------------------|------------------------------------------------------|
| Frontend 502/504                      | Nginx-Logs (`/var/log/nginx/error.log`), Backend up? |
| Backend 500                           | `journalctl -u tick-guard-backend`                   |
| Ollama nicht erreichbar               | `curl http://192.168.178.155:11434/api/tags`         |
| Zertifikat schlägt fehl               | Port 80 offen? DNS korrekt? Certbot-Logs prüfen      |
| Downloads blockiert                   | `CORS_ORIGINS` / Referrer-Checks / JWT-Erneuerung    |

---

Mit diesen Schritten läuft Tick Guard vollständig im lokalen Proxmox-Netzwerk und ist dennoch weltweit via DDNS erreichbar. Frontend und Backend bleiben getrennt, Sicherheitsmaßnahmen (TLS, Firewalls, Rate-Limiting, Auth) sind zentral umgesetzt.

