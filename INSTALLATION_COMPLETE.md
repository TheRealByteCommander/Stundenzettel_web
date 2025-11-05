# 📘 Komplette Installationsanleitung
## Stundenzettel Web - Zeiterfassungssystem für Schmitz Intralogistik GmbH

---

## 📑 Inhaltsverzeichnis

1. [Systemanforderungen](#systemanforderungen)
2. [Schnellstart (Lokale Entwicklung)](#schnellstart-lokale-entwicklung)
3. [Vollständige Installation](#vollständige-installation)
4. [Produktions-Deployment](#produktions-deployment)
5. [Docker-Deployment](#docker-deployment)
6. [Shared Hosting (All-Inkl.com)](#shared-hosting-all-inklcom)
7. [VPS/Cloud Server](#vpscloud-server)
8. [Konfiguration](#konfiguration)
9. [Sicherheit](#sicherheit)
10. [Fehlerbehebung](#fehlerbehebung)
11. [Wartung & Updates](#wartung--updates)

---

## 🔧 Systemanforderungen

### Minimum-Anforderungen

**Server:**
- **Betriebssystem:** Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+) oder Windows 10/11 Server
- **RAM:** 2GB (4GB empfohlen für Production)
- **CPU:** 1 Core (2 Cores empfohlen)
- **Speicher:** 10GB freier Speicherplatz (20GB empfohlen)
- **Netzwerk:** Internetverbindung für Package-Downloads und E-Mail-Versand

**Software:**
- **Python:** 3.11 oder höher
- **Node.js:** 18.x oder höher
- **npm/yarn:** neueste Version
- **MongoDB:** 6.0 oder höher (⚠️ NICHT MySQL - aktuelle Architektur nutzt nur MongoDB)
- **Git:** für Repository-Clone

**⚠️ Hinweis zu MySQL:**
- MySQL wird **NUR** für Migration (einmalig) ODER Legacy PHP-Version verwendet
- Aktuelle Python/FastAPI-Version nutzt **NUR MongoDB**
- Siehe `DATENBANK_ARCHITEKTUR.md` für Details

**Optional (für Production):**
- **Nginx** oder **Apache** als Reverse Proxy
- **SSL-Zertifikat** (Let's Encrypt empfohlen)
- **Systemd** für Service-Management (Linux)
- **Docker** & **Docker Compose** (für Container-Deployment)

---

## 🚀 Schnellstart (Lokale Entwicklung)

### Schritt 1: Voraussetzungen installieren

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nodejs npm mongodb git
```

#### Windows:
1. **Python 3.11+:** https://www.python.org/downloads/
   - ✅ "Add Python to PATH" beim Installieren aktivieren
2. **Node.js 18+:** https://nodejs.org/
3. **MongoDB:** https://www.mongodb.com/try/download/community
4. **Git:** https://git-scm.com/downloads

#### macOS:
```bash
brew install python@3.11 node mongodb-community git
```

### Schritt 2: Repository klonen

```bash
git clone https://github.com/TheRealByteCommander/Stundenzettel_web.git
cd Stundenzettel_web
```

### Schritt 3: Backend einrichten

```bash
cd backend

# Virtual Environment erstellen
python3 -m venv venv

# Virtual Environment aktivieren
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Abhängigkeiten installieren
pip install --upgrade pip
pip install -r requirements.txt
```

### Schritt 4: Backend-Konfiguration

Erstellen Sie die Datei `backend/.env`:

```env
# Datenbank
MONGO_URL=mongodb://localhost:27017
DB_NAME=stundenzettel

# JWT Secret Key (WICHTIG: In Production ändern!)
SECRET_KEY=change-me-to-secure-random-string-min-32-characters

# Optional: Reisekosten-App
LOCAL_RECEIPTS_PATH=C:/Reisekosten_Belege

# Optional: Ollama LLM (für Reisekosten-Prüfung)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Optional: Verschlüsselung für DSGVO-Compliance
ENCRYPTION_KEY=generate-with-python-cryptography-fernet-key
```

**Secret Key generieren:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Encryption Key generieren:**
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Schritt 5: MongoDB starten

**Linux:**
```bash
sudo systemctl start mongod
sudo systemctl enable mongod  # Autostart aktivieren
```

**Windows:**
```bash
net start MongoDB
```

**macOS:**
```bash
brew services start mongodb-community
```

**Docker (Alternative):**
```bash
docker run -d --name mongodb -p 27017:27017 mongo:6.0
```

### Schritt 6: Frontend einrichten

```bash
cd ../frontend

# Abhängigkeiten installieren
npm install
# oder mit yarn:
yarn install
```

### Schritt 7: Frontend-Konfiguration

Erstellen Sie die Datei `frontend/.env`:

```env
REACT_APP_BACKEND_URL=http://localhost:8000
```

### Schritt 8: Anwendung starten

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
# oder: yarn start
```

### Schritt 9: Erste Anmeldung

1. Öffnen Sie: **http://localhost:3000**
2. **E-Mail:** `admin@schmitz-intralogistik.de`
3. **Passwort:** `admin123`
4. ⚠️ **WICHTIG:** Passwort sofort nach erster Anmeldung ändern!
5. 2FA einrichten (obligatorisch)

---

## 📦 Vollständige Installation

### Backend-Installation (Detailliert)

#### 1. Python Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
```

#### 2. Python-Abhängigkeiten

```bash
# Requirements installieren
pip install --upgrade pip
pip install -r requirements.txt

# Optional: Development Tools
pip install black isort flake8 mypy pytest
```

**Wichtige Abhängigkeiten:**
- `fastapi` - Web Framework
- `uvicorn` - ASGI Server
- `motor` / `pymongo` - MongoDB Driver
- `cryptography` - Verschlüsselung (DSGVO)
- `pyotp` - 2FA
- `reportlab` - PDF-Generierung
- `PyPDF2` / `pdfplumber` - PDF-Verarbeitung

#### 3. Umgebungsvariablen (.env)

Vollständige `.env` Beispiel-Datei:

```env
# ============================================
# DATENBANK
# ============================================
MONGO_URL=mongodb://localhost:27017
# Alternative mit Authentifizierung:
# MONGO_URL=mongodb://username:password@localhost:27017/stundenzettel?authSource=admin
DB_NAME=stundenzettel

# ============================================
# SICHERHEIT
# ============================================
# JWT Secret Key (MINDESTENS 32 Zeichen!)
SECRET_KEY=Ihr-Sehr-Geheimer-Secret-Key-Hier-Mindestens-32-Zeichen-Lang

# Verschlüsselungsschlüssel für DSGVO-Compliance (44 Zeichen Base64)
# Generieren mit: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=Ihre-44-Zeichen-Base64-Verschluesselungs-Schluessel-Hier

# ============================================
# REISEKOSTEN-APP
# ============================================
# Lokaler Speicherpfad für PDF-Belege (nur auf Office-Rechner, NICHT Webserver!)
# Windows:
LOCAL_RECEIPTS_PATH=C:/Reisekosten_Belege
# Linux:
# LOCAL_RECEIPTS_PATH=/var/receipts

# ============================================
# OLLAMA LLM (Optional)
# ============================================
# Für automatische Reisekosten-Prüfung
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# ============================================
# DEBUGGING (Nur Development)
# ============================================
# DEBUG=True  # Nur für lokale Entwicklung!
```

#### 4. MongoDB-Konfiguration

**MongoDB starten und konfigurieren:**

```bash
# MongoDB starten
sudo systemctl start mongod

# MongoDB Status prüfen
sudo systemctl status mongod

# Autostart aktivieren
sudo systemctl enable mongod

# MongoDB Shell öffnen (optional)
mongosh
```

**Benutzer erstellen (optional, für Production empfohlen):**

```javascript
// In MongoDB Shell:
use admin
db.createUser({
  user: "stundenzettel_admin",
  pwd: "SicheresPasswort123!",
  roles: [{ role: "readWrite", db: "stundenzettel" }]
})
```

Dann `.env` anpassen:
```env
MONGO_URL=mongodb://stundenzettel_admin:SicheresPasswort123!@localhost:27017/stundenzettel?authSource=admin
```

#### 5. Backend testen

```bash
cd backend
source venv/bin/activate
python -m uvicorn server:app --host 0.0.0.0 --port 8000

# API-Dokumentation öffnen:
# http://localhost:8000/docs
```

### Frontend-Installation (Detailliert)

#### 1. Node.js Version prüfen

```bash
node --version  # Sollte 18.x oder höher sein
npm --version
```

#### 2. Frontend-Abhängigkeiten

```bash
cd frontend

# Mit npm:
npm install

# Oder mit yarn (empfohlen):
npm install -g yarn
yarn install
```

#### 3. Umgebungsvariablen

Erstellen Sie `frontend/.env`:

```env
# Backend API URL
REACT_APP_BACKEND_URL=http://localhost:8000

# Für Production:
# REACT_APP_BACKEND_URL=https://ihre-domain.de/api
```

#### 4. Development Build testen

```bash
npm start
# Öffnet automatisch http://localhost:3000
```

#### 5. Production Build erstellen

```bash
npm run build
# oder: yarn build

# Build-Ordner: frontend/build/
```

---

## 🏭 Produktions-Deployment

### Option A: Linux Server mit Systemd

#### 1. Server vorbereiten

```bash
# System aktualisieren
sudo apt update && sudo apt upgrade -y

# Basis-Pakete installieren
sudo apt install -y python3 python3-pip python3-venv nodejs npm mongodb nginx git
```

#### 2. Anwendung deployen

```bash
# Projekt klonen
cd /opt
sudo git clone https://github.com/TheRealByteCommander/Stundenzettel_web.git
sudo chown -R $USER:$USER Stundenzettel_web
cd Stundenzettel_web

# Backend einrichten
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# .env erstellen (siehe Konfiguration)
nano .env

# Frontend builden
cd ../frontend
npm install
npm run build
```

#### 3. Systemd Service für Backend

Erstellen Sie `/etc/systemd/system/stundenzettel-backend.service`:

```ini
[Unit]
Description=Stundenzettel Backend API
After=network.target mongod.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/Stundenzettel_web/backend
Environment="PATH=/opt/Stundenzettel_web/backend/venv/bin"
ExecStart=/opt/Stundenzettel_web/backend/venv/bin/uvicorn server:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Service aktivieren:

```bash
sudo systemctl daemon-reload
sudo systemctl enable stundenzettel-backend
sudo systemctl start stundenzettel-backend
sudo systemctl status stundenzettel-backend
```

#### 4. Nginx Reverse Proxy

Erstellen Sie `/etc/nginx/sites-available/stundenzettel`:

```nginx
server {
    listen 80;
    server_name ihre-domain.de www.ihre-domain.de;

    # SSL Redirect (nach Let's Encrypt)
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ihre-domain.de www.ihre-domain.de;

    # SSL-Zertifikate (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/ihre-domain.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ihre-domain.de/privkey.pem;
    
    # SSL-Konfiguration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Frontend
    root /opt/Stundenzettel_web/frontend/build;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Static Assets
    location /static {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Aktivieren:

```bash
sudo ln -s /etc/nginx/sites-available/stundenzettel /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 5. SSL-Zertifikat (Let's Encrypt)

```bash
# Certbot installieren
sudo apt install certbot python3-certbot-nginx

# Zertifikat erstellen
sudo certbot --nginx -d ihre-domain.de -d www.ihre-domain.de

# Automatische Erneuerung testen
sudo certbot renew --dry-run
```

#### 6. Firewall konfigurieren

```bash
# UFW Firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### Option B: Windows Server mit IIS

#### 1. Python installieren

1. Python 3.11+ von python.org installieren
2. ✅ "Add Python to PATH" aktivieren
3. IIS mit Python-Handler konfigurieren

#### 2. Backend als Windows Service

Verwenden Sie `NSSM` (Non-Sucking Service Manager):

```bash
# NSSM herunterladen: https://nssm.cc/download
# Service erstellen:
nssm install StundenzettelBackend "C:\Python311\python.exe" "-m" "uvicorn" "server:app" "--host" "127.0.0.1" "--port" "8000"
nssm set StundenzettelBackend AppDirectory "C:\Stundenzettel_web\backend"
nssm start StundenzettelBackend
```

#### 3. IIS Reverse Proxy

Installieren Sie **URL Rewrite** und **Application Request Routing** Module für IIS.

---

## 🐳 Docker-Deployment

### Docker Compose Setup

Erstellen Sie `docker-compose.yml` im Projekt-Root:

```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:6.0
    container_name: stundenzettel-mongodb
    restart: always
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
      - mongodb_config:/data/configdb
    environment:
      - MONGO_INITDB_DATABASE=stundenzettel
    networks:
      - stundenzettel-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: stundenzettel-backend
    restart: always
    ports:
      - "8000:8000"
    environment:
      - MONGO_URL=mongodb://mongodb:27017
      - DB_NAME=stundenzettel
      - SECRET_KEY=${SECRET_KEY}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - LOCAL_RECEIPTS_PATH=/app/receipts
      - OLLAMA_BASE_URL=${OLLAMA_BASE_URL:-http://host.docker.internal:11434}
    volumes:
      - ./backend:/app
      - receipts_data:/app/receipts
    depends_on:
      - mongodb
    networks:
      - stundenzettel-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: stundenzettel-frontend
    restart: always
    ports:
      - "3000:80"
    environment:
      - REACT_APP_BACKEND_URL=http://localhost:8000/api
    depends_on:
      - backend
    networks:
      - stundenzettel-network

volumes:
  mongodb_data:
  mongodb_config:
  receipts_data:

networks:
  stundenzettel-network:
    driver: bridge
```

### Backend Dockerfile

Erstellen Sie `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendung kopieren
COPY . .

# Port freigeben
EXPOSE 8000

# Server starten
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

Erstellen Sie `frontend/Dockerfile`:

```dockerfile
# Build Stage
FROM node:18-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Production Stage
FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Nginx Config für Frontend

Erstellen Sie `frontend/nginx.conf`:

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Docker starten

```bash
# .env für Docker erstellen
cat > .env << EOF
SECRET_KEY=Ihr-Secret-Key-Hier
ENCRYPTION_KEY=Ihr-Encryption-Key-Hier
OLLAMA_BASE_URL=http://host.docker.internal:11434
EOF

# Builden und starten
docker-compose up --build -d

# Logs ansehen
docker-compose logs -f

# Stoppen
docker-compose down
```

---

## 🌐 Shared Hosting (All-Inkl.com)

Siehe `README.md` Abschnitt "Installation auf All-Inkl.com Webserver" für detaillierte Anleitung.

**Kurzfassung:**
1. Verwenden Sie die **PHP-Version** aus dem `webapp/` Ordner
2. Frontend als Static Build deployen
3. MySQL statt MongoDB verwenden
4. `.htaccess` für URL-Rewriting konfigurieren

---

## ☁️ VPS/Cloud Server

### Amazon AWS / Google Cloud / Azure

1. **EC2/VM-Instance erstellen:**
   - Ubuntu 22.04 LTS
   - t2.micro (für Testing) oder t3.small+ (Production)
   - Security Group: Port 22, 80, 443 öffnen

2. **Server einrichten:**
```bash
# SSH-Verbindung
ssh -i your-key.pem ubuntu@your-server-ip

# Script ausführen (siehe unten)
```

### Setup-Script für VPS

Erstellen Sie `setup-vps.sh`:

```bash
#!/bin/bash
set -e

echo "=== Stundenzettel Installation ==="

# System aktualisieren
sudo apt update && sudo apt upgrade -y

# Basis-Pakete
sudo apt install -y python3 python3-pip python3-venv nodejs npm mongodb nginx git

# MongoDB starten
sudo systemctl start mongod
sudo systemctl enable mongod

# Projekt klonen
cd /opt
sudo git clone https://github.com/TheRealByteCommander/Stundenzettel_web.git
sudo chown -R $USER:$USER Stundenzettel_web
cd Stundenzettel_web

# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
npm run build

echo "=== Installation abgeschlossen ==="
echo "Bitte .env Dateien konfigurieren und Services starten!"
```

---

## ⚙️ Konfiguration

### Backend-Umgebungsvariablen (Vollständig)

```env
# ============================================
# DATENBANK
# ============================================
MONGO_URL=mongodb://localhost:27017
DB_NAME=stundenzettel

# ============================================
# SICHERHEIT
# ============================================
SECRET_KEY=Ihr-JWT-Secret-Key-Mindestens-32-Zeichen
ENCRYPTION_KEY=Ihr-Fernet-Key-44-Zeichen-Base64

# ============================================
# REISEKOSTEN-APP
# ============================================
LOCAL_RECEIPTS_PATH=/var/receipts

# ============================================
# OLLAMA LLM
# ============================================
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# ============================================
# CORS (Optional)
# ============================================
# CORS_ORIGINS=http://localhost:3000,https://ihre-domain.de
```

### Frontend-Umgebungsvariablen

```env
REACT_APP_BACKEND_URL=https://ihre-domain.de/api
```

### Erste Konfiguration nach Installation

1. **SMTP konfigurieren** (Admin-Panel):
   - Gmail: `smtp.gmail.com:587`
   - Outlook: `smtp-mail.outlook.com:587`
   - Eigener Server: Server-Hostname und Port

2. **2FA einrichten** (obligatorisch für alle Benutzer)

3. **Benutzer anlegen** (Admin-Panel)

4. **Wochenstunden konfigurieren** (Standard: 40h)

---

## 🔐 Sicherheit

### Production-Checkliste

- [ ] `SECRET_KEY` geändert (min. 32 Zeichen, zufällig)
- [ ] `ENCRYPTION_KEY` generiert und gesetzt
- [ ] Standard-Admin-Passwort geändert
- [ ] SSL/HTTPS aktiviert
- [ ] Firewall konfiguriert
- [ ] MongoDB-Authentifizierung aktiviert
- [ ] `.env` Dateien nicht öffentlich zugänglich
- [ ] Regelmäßige Backups eingerichtet
- [ ] Logs überwacht
- [ ] Updates installiert

### Verschlüsselungsschlüssel generieren

```bash
# Secret Key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Encryption Key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### MongoDB Sicherheit

```javascript
// MongoDB Shell
use admin
db.createUser({
  user: "stundenzettel_user",
  pwd: "SicheresPasswort123!",
  roles: [{ role: "readWrite", db: "stundenzettel" }]
})
```

### Firewall (UFW)

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

---

## 🔧 Fehlerbehebung

### Häufige Probleme

#### Backend startet nicht

```bash
# Logs prüfen
journalctl -u stundenzettel-backend -f

# Port bereits belegt?
sudo netstat -tulpn | grep :8000
sudo lsof -i :8000

# Python-Pfad prüfen
which python3
python3 --version
```

#### MongoDB-Verbindungsfehler

```bash
# MongoDB Status
sudo systemctl status mongod

# MongoDB Logs
sudo journalctl -u mongod -f

# Verbindung testen
mongosh
# oder: mongo (ältere Versionen)

# Port prüfen
sudo netstat -tulpn | grep :27017
```

#### Frontend Build-Fehler

```bash
# Node-Version prüfen
node --version

# node_modules löschen und neu installieren
rm -rf node_modules package-lock.json
npm install

# Cache leeren
npm cache clean --force
```

#### CORS-Fehler

Backend `server.py` prüfen:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://ihre-domain.de"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 2FA-Fehler

- Zeit-Synchronisation prüfen
- Google Authenticator App neu installieren
- 2FA-Secret neu generieren (Admin-Panel)

---

## 🔄 Wartung & Updates

### Regelmäßige Backups

#### MongoDB Backup

```bash
# Backup erstellen
mongodump --uri="mongodb://localhost:27017/stundenzettel" --out=/backup/$(date +%Y%m%d)

# Backup wiederherstellen
mongorestore --uri="mongodb://localhost:27017/stundenzettel" /backup/20240101
```

#### Automatisches Backup-Script

Erstellen Sie `/usr/local/bin/backup-stundenzettel.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backup/stundenzettel"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# MongoDB Backup
mongodump --uri="mongodb://localhost:27017/stundenzettel" --out=$BACKUP_DIR/mongodb_$DATE

# .env Backups
cp /opt/Stundenzettel_web/backend/.env $BACKUP_DIR/env_$DATE

# Alte Backups löschen (älter als 30 Tage)
find $BACKUP_DIR -type d -mtime +30 -exec rm -rf {} +
```

Cronjob einrichten:
```bash
# Crontab bearbeiten
crontab -e

# Tägliches Backup um 2 Uhr morgens
0 2 * * * /usr/local/bin/backup-stundenzettel.sh
```

### Updates installieren

```bash
cd /opt/Stundenzettel_web

# Änderungen pullen
git pull origin main

# Backend aktualisieren
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Frontend aktualisieren
cd ../frontend
npm install
npm run build

# Services neu starten
sudo systemctl restart stundenzettel-backend
sudo systemctl reload nginx
```

### Logs überwachen

```bash
# Backend-Logs
sudo journalctl -u stundenzettel-backend -f

# Nginx-Logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# MongoDB-Logs
sudo tail -f /var/log/mongodb/mongod.log
```

---

## 📞 Support & Hilfe

### Standard-Anmeldedaten

- **E-Mail:** `admin@schmitz-intralogistik.de`
- **Passwort:** `admin123`
- ⚠️ **SOFORT nach Installation ändern!**

### Nützliche URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API-Dokumentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

### Dokumentation

- **README.md** - Projekt-Übersicht
- **CHANGELOG.md** - Änderungshistorie
- **DSGVO_COMPLIANCE.md** - Datenschutz-Compliance
- **SECURITY.md** - Sicherheitsrichtlinien
- **AGENTS_README.md** - Agent-Netzwerk-Dokumentation

### Bei Problemen

1. Logs prüfen
2. Konfiguration überprüfen
3. Dokumentation durchlesen
4. GitHub Issues prüfen
5. Support kontaktieren

---

## ✅ Installations-Checkliste

Nach der Installation:

- [ ] MongoDB läuft
- [ ] Backend startet erfolgreich
- [ ] Frontend lädt ohne Fehler
- [ ] Login funktioniert
- [ ] 2FA eingerichtet
- [ ] SMTP konfiguriert
- [ ] Erster Benutzer angelegt
- [ ] Test-Stundenzettel erstellt
- [ ] PDF-Generierung funktioniert
- [ ] E-Mail-Versand funktioniert
- [ ] SSL/HTTPS aktiviert (Production)
- [ ] Backups eingerichtet
- [ ] Firewall konfiguriert
- [ ] Logs überwacht

---

**Installation abgeschlossen! 🎉**

Bei Fragen oder Problemen siehe Fehlerbehebung oder kontaktieren Sie den Support.

