# 📋 Installationsanleitung - Ihr spezifisches Setup

## Ihre Architektur

```
┌─────────────────────────────────────────────────────────────┐
│  All-inkl.com Webserver                                     │
│  Domain: stundenzettel.byte-commander.de                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Frontend (React Build)                             │   │
│  │  - Statische Dateien                                │   │
│  └───────────────────────┬─────────────────────────────┘   │
│                          │ HTTPS                            │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           │ API-Calls über Internet
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Proxmox Server (Heimnetz)                                  │
│  IP: 192.168.178.154                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Backend API (FastAPI)                              │   │
│  │  - Port 8000 (öffentlich erreichbar)                │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │ MongoDB (lokal oder remote)                 │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │ Agent Container (lokal)                     │   │   │
│  │  └───────────────────┬─────────────────────────┘   │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │ Local Storage                               │   │   │
│  │  │ /var/stundenzettel/receipts                 │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  └───────────────────────┬─────────────────────────────┘   │
└──────────────────────────┼──────────────────────────────────┘
                           │ HTTP API (lokal)
                           │ Port 11434
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  GMKTec evo x2 (Heimnetz)                                   │
│  IP: 192.168.178.155                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Ollama LLM Server                                  │   │
│  │  - Port 11434                                       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## ⚠️ WICHTIG: All-inkl.com Regeln gelten NUR für Frontend

**Ihre Architektur:**
- ✅ **Frontend auf All-inkl.com**: Nur statische Dateien (React Build)
- ✅ **Backend auf Proxmox**: Komplett unabhängig von All-inkl-Regeln

**Was bedeutet das?**
- ❌ **Keine All-inkl-Regeln für Backend**: Backend läuft auf Proxmox, nicht auf All-inkl
- ✅ **All-inkl-Regeln nur für Frontend**: Nur für statische Dateien-Hosting relevant
- ✅ **Backend-Konfiguration**: Vollständig auf Proxmox (Python, FastAPI, MongoDB, etc.)
- ✅ **Keine PHP/Limits auf Backend**: Backend ist Python/FastAPI, keine All-inkl-Limits

**All-inkl-Regeln sind nur relevant für:**
1. Frontend-Build-Upload (statische Dateien)
2. `.htaccess` für React Router Support (optional)
3. Upload-Limits beim Hochladen des Frontend-Builds (einmalig)

**Backend-Regeln (auf Proxmox):**
- Keine All-inkl-Limits
- Volle Python-Umgebung
- Eigene Firewall-Regeln
- Eigene Docker-Container
- Eigene MongoDB-Instanz
- Keine Upload-Limits

---

## Installation Schritt für Schritt

### Teil 1: Frontend auf All-inkl.com (nur statische Dateien)

**Auf Ihrem Entwicklungsrechner:**

```powershell
cd C:\Users\mschm\Stundenzettel_web\frontend

# .env Datei erstellen
Set-Content .env "REACT_APP_BACKEND_URL=https://proxmox-public-ip-oder-domain:8000"

# Oder falls Sie eine Domain für Proxmox haben:
# Set-Content .env "REACT_APP_BACKEND_URL=https://api.byte-commander.de"

# Build erstellen
npm install --legacy-peer-deps
npm run build
```

**Wichtig:** Die URL muss auf den Proxmox-Server zeigen, der öffentlich erreichbar sein muss!

#### Schritt 1.2: Build auf All-inkl hochladen

**Via FTP/SFTP:**

1. **Verbinden Sie sich mit All-inkl:**
   - FTP-Host: `ftp.stundenzettel.byte-commander.de` (oder wie in All-inkl angegeben)
   - Benutzername: Ihr All-inkl Kürzel
   - Passwort: Ihr FTP-Passwort

2. **Upload-Verzeichnis:** `/html/` oder `/html/stundenzettel/`

3. **Upload den Inhalt von `frontend/build/`:**
   ```
   /html/
   ├── index.html
   ├── static/
   │   ├── css/
   │   └── js/
   ├── manifest.json
   └── ...
   ```

#### Schritt 1.3: .htaccess auf All-inkl konfigurieren (optional)

**Hinweis:** Dies ist nur für das Frontend (statische Dateien) relevant, nicht für das Backend!

**Erstellen Sie `/html/.htaccess`:**

```apache
# React Router Support
RewriteEngine On
RewriteBase /

# API-Routes weiterleiten (falls Backend-Proxy gewünscht)
# RewriteRule ^api/(.*)$ https://proxmox-public-ip:8000/api/$1 [P,L]

# Frontend-Routes (React Router)
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^ index.html [L]

# Security Headers
Header always set X-Content-Type-Options "nosniff"
Header always set X-Frame-Options "DENY"
Header always set X-XSS-Protection "1; mode=block"
```

---

### Teil 2: Backend auf Proxmox Server

#### Schritt 2.1: Proxmox vorbereiten

**SSH auf Proxmox (192.168.178.154):**

```bash
# System aktualisieren
sudo apt update && sudo apt upgrade -y

# Python 3.11+ installieren
sudo apt install python3.11 python3.11-venv python3-pip -y

# Oder Docker installieren (empfohlen für Container)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER
```

#### Schritt 2.2: Projekt auf Proxmox kopieren

**Option A: Git Clone**

```bash
# Auf Proxmox
cd /opt
sudo git clone https://github.com/TheRealByteCommander/Stundenzettel_web.git
sudo chown -R $USER:$USER Stundenzettel_web
cd Stundenzettel_web
```

**Option B: Dateien hochladen (FTP/SFTP/SCP)**

```bash
# Von Ihrem PC zu Proxmox
scp -r C:\Users\mschm\Stundenzettel_web user@192.168.178.154:/opt/
```

#### Schritt 2.3: Backend einrichten

```bash
cd /opt/Stundenzettel_web/backend

# Virtual Environment erstellen
python3.11 -m venv venv
source venv/bin/activate

# Dependencies installieren
pip install --upgrade pip
pip install -r requirements.txt
```

#### Schritt 2.4: Backend .env konfigurieren

**Erstellen Sie `backend/.env`:**

```env
# ============================================
# DATENBANK
# ============================================
MONGO_URL=mongodb://localhost:27017
DB_NAME=stundenzettel

# ============================================
# SICHERHEIT
# ============================================
SECRET_KEY=Ihr-Sehr-Geheimer-Secret-Key-Hier-Mindestens-32-Zeichen-Lang
ENCRYPTION_KEY=<Generieren Sie mit: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">

# ============================================
# REISEKOSTEN-APP
# ============================================
# Lokaler Speicher auf Proxmox
LOCAL_RECEIPTS_PATH=/var/stundenzettel/receipts

# ============================================
# OLLAMA LLM (GMKTec im Heimnetzwerk)
# ============================================
OLLAMA_BASE_URL=http://192.168.178.155:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=300
OLLAMA_MAX_RETRIES=3
OLLAMA_RETRY_DELAY=2.0
```

#### Schritt 2.5: Verzeichnis für Receipts erstellen

```bash
# Auf Proxmox
sudo mkdir -p /var/stundenzettel/receipts
sudo mkdir -p /var/stundenzettel/receipts/signed_timesheets
sudo chown -R $USER:$USER /var/stundenzettel
chmod -R 755 /var/stundenzettel
```

#### Schritt 2.6: MongoDB installieren

**Option A: MongoDB lokal auf Proxmox**

```bash
# MongoDB installieren
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt update
sudo apt install -y mongodb-org

# MongoDB starten
sudo systemctl start mongod
sudo systemctl enable mongod
```

**Option B: MongoDB Atlas (Remote, Cloud)**

```env
# In backend/.env
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/stundenzettel?retryWrites=true&w=majority
```

#### Schritt 2.7: Systemd Service erstellen

**Erstellen Sie `/etc/systemd/system/stundenzettel-backend.service`:**

```ini
[Unit]
Description=Stundenzettel Backend API
After=network.target mongod.service

[Service]
Type=simple
User=ihr-benutzername
WorkingDirectory=/opt/Stundenzettel_web/backend
Environment="PATH=/opt/Stundenzettel_web/backend/venv/bin"
EnvironmentFile=/opt/Stundenzettel_web/backend/.env
ExecStart=/opt/Stundenzettel_web/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Service aktivieren:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable stundenzettel-backend
sudo systemctl start stundenzettel-backend
sudo systemctl status stundenzettel-backend
```

---

### Teil 3: Firewall & Netzwerk konfigurieren

#### Schritt 3.1: Proxmox Firewall (Port 8000 öffnen)

**Auf Proxmox:**

```bash
# UFW aktivieren
sudo ufw enable

# Port 8000 für Backend-API öffnen (öffentlich)
sudo ufw allow 8000/tcp

# Port 22 für SSH (sollte bereits offen sein)
sudo ufw allow 22/tcp

# Status prüfen
sudo ufw status
```

**WICHTIG:** Proxmox muss öffentlich erreichbar sein!

#### Schritt 3.2: Router Port-Forwarding

**In Ihrem Router (FritzBox/Router-Admin):**

1. **Port-Weiterleitung einrichten:**
   - Externer Port: `8000` (oder anderer, z.B. `8443`)
   - Interner Port: `8000`
   - Interner Host: `192.168.178.154` (Proxmox)
   - Protokoll: TCP

2. **Optional: Domain/DNS für Proxmox:**
   - Dynamisches DNS (DDNS) einrichten
   - Oder: Statische IP beim Provider beantragen
   - Beispiel: `api.byte-commander.de` → Ihre öffentliche IP

#### Schritt 3.3: Frontend .env aktualisieren

**Nachdem Port-Forwarding funktioniert:**

```env
# frontend/.env (vor Build)
REACT_APP_BACKEND_URL=https://ihre-oeffentliche-ip:8000
# Oder mit Domain:
# REACT_APP_BACKEND_URL=https://api.byte-commander.de
```

**Dann Frontend neu builden und hochladen!**

---

### Teil 4: GMKTec evo x2 einrichten

#### Schritt 4.1: Ollama installieren

**Auf GMKTec (192.168.178.155):**

```bash
# Ollama installieren
curl -fsSL https://ollama.ai/install.sh | sh

# Ollama als Service starten
sudo systemctl enable ollama
sudo systemctl start ollama

# Modell herunterladen
ollama pull llama3.2
```

#### Schritt 4.2: Ollama für Netzwerk-Zugriff konfigurieren

**Standardmäßig hört Ollama auf `0.0.0.0:11434`, also sollte es bereits erreichbar sein.**

**Firewall prüfen:**

```bash
# UFW (Ubuntu/Debian)
sudo ufw allow from 192.168.178.154 to any port 11434

# Firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="192.168.178.154" port protocol="tcp" port="11434" accept'
sudo firewall-cmd --reload
```

#### Schritt 4.3: Statische IP für GMKTec

**Im Router konfigurieren:**

- DHCP-Reservation für GMKTec MAC-Adresse
- Statische IP: `192.168.178.155`

**Oder auf GMKTec selbst (Linux):**

```bash
# Statische IP konfigurieren
sudo nano /etc/netplan/50-cloud-init.yaml
# Oder
sudo nano /etc/network/interfaces
```

---

### Teil 5: HTTPS/SSL für Backend

#### Schritt 5.1: Nginx Reverse Proxy auf Proxmox

**Nginx installieren:**

```bash
sudo apt install nginx certbot python3-certbot-nginx
```

#### Schritt 5.2: Nginx Konfiguration

**Erstellen Sie `/etc/nginx/sites-available/stundenzettel-api`:**

```nginx
server {
    listen 80;
    server_name api.byte-commander.de;  # Ihre Domain für API (optional)
    # Oder ohne Domain, nur Port 8000 direkt verwenden

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket Support (falls benötigt)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts für längere Requests (Agent-Verarbeitung)
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
    }
}
```

**Alternative: Direkt Port 8000 verwenden (ohne Nginx)**

Falls Sie keine Domain haben, können Sie direkt Port 8000 verwenden:
- Frontend `.env`: `REACT_APP_BACKEND_URL=https://ihre-oeffentliche-ip:8000`
- Router Port-Forwarding: 8000 → 192.168.178.154:8000

**Aktivieren:**

```bash
sudo ln -s /etc/nginx/sites-available/stundenzettel-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Schritt 5.3: SSL-Zertifikat (Let's Encrypt)

```bash
sudo certbot --nginx -d api.byte-commander.de
```

**Dann Frontend `.env` aktualisieren:**

```env
REACT_APP_BACKEND_URL=https://api.byte-commander.de
```

---

## Konfiguration-Zusammenfassung

### All-inkl.com (Frontend)

**Datei:** `frontend/.env` (vor Build)

```env
REACT_APP_BACKEND_URL=https://api.byte-commander.de
# oder
REACT_APP_BACKEND_URL=https://ihre-oeffentliche-ip:8000
```

**Nach Build:** Upload `build/` nach All-inkl `/html/`

### Proxmox (Backend + Agents)

**Datei:** `backend/.env`

```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=stundenzettel
SECRET_KEY=...
ENCRYPTION_KEY=...
LOCAL_RECEIPTS_PATH=/var/stundenzettel/receipts
OLLAMA_BASE_URL=http://192.168.178.155:11434
OLLAMA_MODEL=llama3.2
```

**Services:**
- Backend: `systemctl start stundenzettel-backend`
- MongoDB: `systemctl start mongod`

### GMKTec (Ollama)

**Konfiguration:** Standard (hört auf `0.0.0.0:11434`)

**Firewall:** Port 11434 für `192.168.178.154` (Proxmox) erlauben

---

## Verifikation

### 1. Frontend testen

1. Öffnen Sie: `https://stundenzettel.byte-commander.de`
2. Prüfen Sie Browser-Console (F12)
3. API-Calls sollten zu Backend gehen

### 2. Backend testen

```bash
# Vom Proxmox aus
curl http://localhost:8000/health

# Von außen (Ihr PC)
curl https://api.byte-commander.de/health
```

### 3. Ollama testen

```bash
# Vom Proxmox aus
curl http://192.168.178.155:11434/api/tags

# Sollte JSON mit verfügbaren Modellen zurückgeben
```

### 4. MongoDB testen

```bash
# Auf Proxmox
mongosh
# Oder
mongo
# Sollte MongoDB Shell öffnen
```

---

## Troubleshooting

### Problem: Frontend kann Backend nicht erreichen

**Lösung:**
1. Prüfen Sie CORS-Einstellungen im Backend
2. Prüfen Sie Firewall (Port 8000)
3. Prüfen Sie Router Port-Forwarding
4. Testen Sie: `curl https://api.byte-commander.de/health`

### Problem: Backend kann Ollama nicht erreichen

**Lösung:**
1. Prüfen Sie GMKTec IP: `ping 192.168.178.155`
2. Prüfen Sie Ollama läuft: `curl http://192.168.178.155:11434/api/tags`
3. Prüfen Sie Firewall auf GMKTec

### Problem: MongoDB-Verbindung fehlgeschlagen

**Lösung:**
1. MongoDB läuft? `sudo systemctl status mongod`
2. Verbindung testen: `mongosh`
3. `MONGO_URL` in `.env` korrekt?

---

## Checkliste

### All-inkl.com
- [ ] Frontend Build erstellt mit korrekter `REACT_APP_BACKEND_URL`
- [ ] Build auf All-inkl hochgeladen
- [ ] `.htaccess` konfiguriert
- [ ] Frontend erreichbar: `https://stundenzettel.byte-commander.de`

### Proxmox (192.168.178.154)
- [ ] Projekt kopiert nach `/opt/Stundenzettel_web`
- [ ] Virtual Environment erstellt
- [ ] Dependencies installiert
- [ ] `.env` Datei konfiguriert
- [ ] MongoDB installiert und gestartet
- [ ] Verzeichnis `/var/stundenzettel/receipts` erstellt
- [ ] Systemd Service erstellt und gestartet
- [ ] Firewall: Port 8000 geöffnet
- [ ] Backend erreichbar: `http://localhost:8000/health`

### Router
- [ ] Port-Forwarding: Port 8000 → 192.168.178.154
- [ ] Optional: DDNS für Proxmox Domain
- [ ] GMKTec: Statische IP (192.168.178.155) reserviert

### GMKTec (192.168.178.155)
- [ ] Ollama installiert
- [ ] Ollama Service gestartet
- [ ] Modell `llama3.2` heruntergeladen
- [ ] Firewall: Port 11434 für 192.168.178.154 erlaubt
- [ ] Ollama erreichbar: `curl http://192.168.178.155:11434/api/tags`

### Optional: HTTPS
- [ ] Nginx installiert auf Proxmox
- [ ] Domain `api.byte-commander.de` zeigt auf Proxmox
- [ ] SSL-Zertifikat (Let's Encrypt) installiert
- [ ] Frontend `.env` mit HTTPS-URL aktualisiert

---

## Nächste Schritte

1. **Erste Anmeldung testen:**
   - URL: `https://stundenzettel.byte-commander.de`
   - Login: `admin@schmitz-intralogistik.de`
   - Passwort: `admin123`

2. **2FA einrichten** (obligatorisch)

3. **SMTP konfigurieren** (für E-Mail-Versand)

4. **Ersten Test-Stundenzettel erstellen**

---

**Installation abgeschlossen! 🎉**

Bei Fragen siehe:
- [ARCHITEKTUR_ALL_INKL_PROXMOX.md](ARCHITEKTUR_ALL_INKL_PROXMOX.md)
- [INSTALLATION_COMPLETE.md](INSTALLATION_COMPLETE.md)

