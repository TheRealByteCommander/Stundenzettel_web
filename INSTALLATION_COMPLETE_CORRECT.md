# 📘 Komplette Installationsanleitung – Lokale Proxmox-Architektur

## ⚠️ Architektur im Überblick

Die empfohlene Produktionsarchitektur nutzt zwei Proxmox-Container im lokalen Netzwerk plus den GMKTec evo x2 für die LLM-Verarbeitung:

```
┌───────────────────────────────────────────────────────────────┐
│            Proxmox Host (lokales Rechenzentrum/VPN)           │
│                                                               │
│  ┌──────────────┐                          ┌────────────────┐ │
│  │ Container 1  │                          │  Container 2   │ │
│  │ Frontend     │  <─── interne HTTP ───>  │ Backend & DB   │ │
│  │ - Nginx/SPA  │                          │ - FastAPI      │ │
│  │ - TLS/Proxy  │                          │ - Agents       │ │
│  └─────┬────────┘                          │ - MongoDB      │ │
│        │ HTTPS (DDNS/WireGuard)            │ - Storage      │ │
│        ▼                                   └────────┬───────┘ │
│  Externe Clients                                   │          │
└─────────────────────────────────────────────────────┼──────────┘
                                                      │
                                                      │ HTTP (LAN/VPN)
                                                      ▼
                                   ┌────────────────────────────────┐
                                   │  GMKTec evo x2 (Ollama Server) │
                                   │  - Port 11434                  │
                                   │  - Llama-Modelle               │
                                   └────────────────────────────────┘
```

- **Container 1 – Frontend-Gateway:** Liefert den React-Build (Nginx oder Caddy) und terminiert HTTPS für den externen Zugriff über DDNS/WireGuard.
- **Container 2 – Backend-Stack:** Enthält FastAPI, Agents, MongoDB sowie das verschlüsselte Dateilager für Belege.
- **GMKTec evo x2:** Betreibt Ollama und stellt die LLM-Funktionen über das lokale Netzwerk bereit (empfohlen via WireGuard oder dediziertem LAN).

Alle Komponenten bleiben innerhalb des lokalen Netzwerks, lediglich Port `443` des Frontend-Containers wird nach außen veröffentlicht (bzw. via VPN erreichbar gemacht).

---

## 📍 Aufgabenverteilung

| Komponente              | Ort                 | Dienst(e)                           | Ports extern |
|------------------------|---------------------|-------------------------------------|--------------|
| Frontend-Gateway       | Proxmox Container 1 | Nginx/Caddy, React Build, TLS       | 443 (HTTPS)  |
| Backend & Datenhaltung | Proxmox Container 2 | FastAPI, Agents, MongoDB, Storage   | keine        |
| LLM                    | GMKTec evo x2       | Ollama                              | keine        |
| VPN/DDNS               | je nach Setup       | WireGuard (empfohlen)               | optional     |

---

## 🛠️ Vorbereitung

1. **DNS/VPN planen**
   - DDNS-Domain auf die öffentliche IP des Frontend-Containers oder des vorgeschalteten Routers legen.
   - WireGuard-Tunnel für administrative Zugriffe einrichten (Port 51820 o. Ä.).
2. **Proxmox-Container anlegen**
   - Zwei LXC- oder KVM-Container mit Ubuntu 22.04+ (oder vergleichbar).
   - Frontend-Container: 1 vCPU, 1–2 GB RAM, 10 GB SSD.
   - Backend-Container: 2–4 vCPU, 4–8 GB RAM, 40 GB SSD (abhängig von Datenvolumen).
3. **GMKTec vorbereiten**
   - Statische IP oder DHCP-Reservierung vergeben (z. B. `192.168.178.155`).
   - WireGuard/VLAN festlegen, falls GMKTec nicht im gleichen Netzsegment steht.

---

## ⚙️ Automatisierte Installation (Empfohlen)

Wer die komplette Einrichtung ohne manuelle Zwischenschritte durchführen möchte, kann die Shell-Skripte aus `scripts/` direkt auf den Containern ausführen. Standardmäßig wird von folgender Topologie ausgegangen: Frontend-CT `192.168.178.150`, Backend-CT `192.168.178.151`, GMKTec/Ollama `192.168.178.155`. Abweichende Werte lassen sich per Umgebungsvariablen setzen.

**Backend-CT**

```bash
curl -fsSL https://raw.githubusercontent.com/TheRealByteCommander/Stundenzettel_web/main/scripts/install_backend_ct.sh \
 | sudo FRONTEND_IP=192.168.178.150 BACKEND_IP=192.168.178.151 OLLAMA_IP=192.168.178.155 \
   DDNS_DOMAIN=192.168.178.150 CORS_ORIGINS=http://192.168.178.150 bash
```

**Frontend-CT**

```bash
curl -fsSL https://raw.githubusercontent.com/TheRealByteCommander/Stundenzettel_web/main/scripts/install_frontend_ct.sh \
 | sudo FRONTEND_IP=192.168.178.150 PUBLIC_HOST=192.168.178.150 \
   BACKEND_HOST=192.168.178.151 BACKEND_PORT=8000 BACKEND_SCHEME=http bash
```

Für eine automatische Let’s-Encrypt-Integration `RUN_CERTBOT=true` sowie `CERTBOT_EMAIL=<adresse>` ergänzen (nur sinnvoll, wenn später ein Domainname hinterlegt ist). Die nachfolgenden Abschnitte beschreiben weiterhin sämtliche Arbeitsschritte, falls einzelne Komponenten manuell angepasst werden sollen.

---

## 🚀 Schritt-für-Schritt Installation

### 1. Container 2 – Backend & MongoDB

```bash
# Basis-Pakete
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git build-essential

# Projekt ablegen
sudo mkdir -p /opt/tick-guard && sudo chown $USER:$USER /opt/tick-guard
cd /opt/tick-guard
git clone <REPO_URL> stundenzettel_web
cd stundenzettel_web/backend

# Python-Umgebung
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### MongoDB installieren

```bash
sudo apt install -y mongodb
# oder Docker:
# docker run -d --name mongodb -p 127.0.0.1:27017:27017 -v /var/lib/mongodb:/data/db mongo:7
```

#### Dateispeicher

```bash
sudo mkdir -p /var/tick-guard/receipts
sudo chown $USER:$USER /var/tick-guard/receipts
```

#### `.env` im Backend

```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=stundenzettel
LOCAL_RECEIPTS_PATH=/var/tick-guard/receipts
SECRET_KEY=<openssl rand -hex 32>
ENCRYPTION_KEY=<openssl rand -hex 32>
OLLAMA_BASE_URL=http://192.168.178.155:11434
OLLAMA_MODEL=llama3.2
OLLAMA_MODEL_CHAT=llama3.2
OLLAMA_MODEL_DOCUMENT=mistral-nemo
OLLAMA_MODEL_ACCOUNTING=llama3.1
OLLAMA_TIMEOUT=300
OLLAMA_MAX_RETRIES=3
CORS_ORIGINS=https://ddns-beispiel.meinedomain.de,https://frontend.local
```

> Referenz-IP-Plan: Frontend-CT `192.168.178.150`, Backend-CT `192.168.178.151`, GMKTec `192.168.178.155`. `CORS_ORIGINS` auf deine Domains/IPs anpassen.

#### Systemd-Service

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

[Install]
WantedBy=multi-user.target
```

```bash
sudo useradd --system --home /opt/tick-guard --shell /usr/sbin/nologin tickguard
sudo chown -R tickguard:tickguard /opt/tick-guard
sudo systemctl daemon-reload
sudo systemctl enable --now tick-guard-backend
sudo systemctl status tick-guard-backend --no-pager
sudo -u tickguard /opt/tick-guard/stundenzettel_web/backend/venv/bin/uvicorn --version
curl http://localhost:8000/health   # Funktionstest
```

### 2. Container 1 – Frontend & Reverse Proxy

```bash
sudo apt update
sudo apt install -y nginx nodejs npm git
```

#### Frontend bauen

```bash
cd /opt/tick-guard
git clone <REPO_URL> stundenzettel_web-frontend
cd stundenzettel_web-frontend/frontend
npm install
echo "REACT_APP_BACKEND_URL=https://ddns-beispiel.meinedomain.de" > .env.production
npm run build
```

#### Build bereitstellen

```bash
sudo rm -rf /var/www/tick-guard
sudo mkdir -p /var/www/tick-guard
sudo cp -r build/* /var/www/tick-guard/
sudo chown -R www-data:www-data /var/www/tick-guard
```

#### Nginx-Konfiguration

```nginx
# /etc/nginx/sites-available/tick-guard
server {
    listen 80;
    server_name ddns-beispiel.meinedomain.de;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ddns-beispiel.meinedomain.de;

    ssl_certificate     /etc/letsencrypt/live/ddns-beispiel.meinedomain.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ddns-beispiel.meinedomain.de/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;

    # PWA/Static Assets
    root /var/www/tick-guard;
    index index.html;

    location / {
        try_files $uri /index.html;
    }

    # API-Proxy ins interne Backend (Container 2)
    location /api/ {
        proxy_pass http://192.168.178.151:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/tick-guard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Zertifikate via Let’s Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d ddns-beispiel.meinedomain.de
```

> Wenn ausschließlich WireGuard genutzt wird und kein öffentlicher Port verfügbar ist, stattdessen interne Zertifizierungsstelle oder selbstsignierte Zertifikate verwenden.

---

### 3. GMKTec evo x2 – Ollama

```bash
curl -fsSL https://ollama.ai/install.sh | sh
sudo systemctl enable --now ollama
ollama pull llama3.2
```

Firewall anpassen:

```bash
sudo ufw allow from 192.168.178.151 to any port 11434 proto tcp
```

Test vom Backend-Container:

```bash
curl http://192.168.178.155:11434/api/tags
```

---

## ✅ Checkliste

- [ ] Beide Container laufen, führen automatische Updates durch (`unattended-upgrades`).
- [ ] Backend-Service aktiv (`systemctl status tick-guard-backend`).
- [ ] MongoDB gesichert (Zugriff nur `127.0.0.1`, regelmäßige Dumps).
- [ ] Frontend über DDNS erreichbar (`https://ddns-beispiel.meinedomain.de`).
- [ ] WireGuard-Clients verbinden erfolgreich und erreichen Backend/Frontend intern.
- [ ] Ollama antwortet innerhalb von <1 s auf `/api/tags`.
- [ ] Push-Benachrichtigungen und E-Mail-Versand getestet.
- [ ] Backup-Strategie eingerichtet (`mongodump`, Receipts-Verzeichnis, Systemd-Services).

---

## 🔐 Sicherheit & Härtung

- **Ports:** Nur `443/tcp` (HTTPS) von außen. SSH ausschließlich via WireGuard/VPN oder per Port-Knocking.
- **Firewall:** `ufw default deny incoming`, explizite Allow-Regeln für WireGuard und HTTPS.
- **Reverse Proxy:** Aktivierte HTTP-Security-Header, Rate-Limiting (`limit_req`), optional WAF (CrowdSec, Naxsi).
- **Secrets:** `.env`-Dateien nur root-lesbar; idealerweise im Secret-Manager (Vault, SOPS) hinterlegt.
- **CORS:** Nur DDNS-Domain + interne Admin-Hosts erlauben.
- **Logging:** Systemd-Journal forwarden, Fail2ban aktivieren, Audit-Logs regelmäßig archivieren.

---

## 🧪 Validierung

1. Login mit Standard-Admin (`admin@schmitz-intralogistik.de` / `admin123`) und Passwortwechsel erzwingen.
2. Timesheet erstellen, PDF herunterladen, Signatur-Upload testen.
3. Reisekosten-Report erzeugen und vom Agenten prüfen lassen (Ollama-Aufruf).
4. Push-Benachrichtigungen (VAPID), SMTP-Versand und 2FA aktivieren.

---

## 📚 Weiterführende Ressourcen

- `ARCHITEKTUR_ALL_INKL_PROXMOX.md` – aktualisierte Architekturübersicht (jetzt ohne All-inkl).
- `backend/LLM_INTEGRATION.md` – Deep-Dive in Agenten & Ollama.
- `OFFICE_RECHNER_ROUTING.md` – Tipps zu Routing, VPN und dynamischen IPs.
- `DSGVO_COMPLIANCE.md` – Datenschutz, Verschlüsselung & Aufbewahrung.

Mit dieser Anleitung betreibst du Tick Guard vollständig lokal, ohne externe Hosting-Anbieter. Der Frontend-Container fungiert als sicherer Gateway, während der Backend-Container alle sensiblen Daten im LAN verarbeitet. Die GMKTec-eigene LLM-Infrastruktur bleibt strikt im internen Netzwerk oder im WireGuard-VPN eingeschlossen.

