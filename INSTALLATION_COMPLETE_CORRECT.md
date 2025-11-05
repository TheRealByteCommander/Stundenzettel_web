# 📘 Komplette Installationsanleitung - Korrekt

## ⚠️ WICHTIG: Architektur-Verständnis

**Diese Anwendung besteht aus mehreren Komponenten, die auf verschiedenen Servern laufen:**

```
┌─────────────────────────────────────────────────────────────┐
│                     All-inkl.com Webserver                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Frontend (React Build) - NUR statische Dateien    │   │
│  │  - HTML, CSS, JavaScript                            │   │
│  │  - Keine Backend-Logik!                            │   │
│  └───────────────────────┬─────────────────────────────┘   │
│                          │ HTTPS                            │
│                          │ API-Calls                        │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Proxmox Server                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Backend API (Python/FastAPI)                      │   │
│  │  - Läuft auf Port 8000 (öffentlich erreichbar)     │   │
│  │  - REST API für Frontend                           │   │
│  └──────┬───────────────────────────────────────┬──────┘   │
│         │                                       │           │
│         ▼                                       ▼           │
│  ┌───────────────────┐          ┌──────────────────────┐ │
│  │  MongoDB          │          │  Agents (Python)     │ │
│  │  - Datenbank      │          │  - Läuft lokal       │ │
│  │  - Auf Proxmox    │          │  - Kein separater    │ │
│  │    oder remote    │          │    Container nötig!  │ │
│  └───────────────────┘          └──────────┬───────────┘ │
│                                             │              │
│                                             │ HTTP API     │
│                                             │ (lokales     │
└─────────────────────────────────────────────┼──────────────┘
                                              │
                                              ▼
                              ┌──────────────────────────┐
                              │  GMKTec evo x2           │
                              │  (Home-Netzwerk)         │
                              │  ┌────────────────────┐  │
                              │  │ Ollama LLM Server  │  │
                              │  │ Port 11434         │  │
                              │  └────────────────────┘  │
                              └──────────────────────────┘
```

## 📍 Wo wird was installiert?

### 1. Frontend (React) → **All-inkl.com Webserver**

**Was wird installiert:**
- Nur die **statischen Dateien** aus dem React Build (`frontend/build/`)
- HTML, CSS, JavaScript-Dateien
- Keine Backend-Logik
- Keine Python/Node.js-Laufzeit nötig

**Installation:**
1. Frontend lokal bauen: `npm run build`
2. Inhalt von `frontend/build/` auf All-inkl hochladen
3. `.htaccess` Datei für React Router hochladen

**Konfiguration:**
- `.env` Datei vor Build: `REACT_APP_BACKEND_URL=https://proxmox-domain.de:8000`
- Oder: `REACT_APP_BACKEND_URL=https://proxmox-ip:8000`

---

### 2. Backend (Python/FastAPI) → **Proxmox Server** ⚠️ NICHT auf All-inkl!

**Was wird installiert:**
- Python 3.11+ Laufzeit
- FastAPI-Anwendung (`backend/server.py`)
- Alle Python-Dependencies (`requirements.txt`)
- MongoDB (lokal oder remote)

**Installation auf Proxmox:**

**Option A: Direkt auf Proxmox VM/Container**

```bash
# 1. VM oder LXC Container erstellen (Ubuntu 22.04+)
# 2. Python installieren
sudo apt update
sudo apt install python3.11 python3-pip python3-venv

# 3. Projekt klonen
cd /opt
git clone <repository-url> stundenzettel_web
cd stundenzettel_web/backend

# 4. Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate

# 5. Dependencies installieren
pip install -r requirements.txt

# 6. .env Datei erstellen
nano .env
```

**.env Konfiguration (auf Proxmox):**
```env
# MongoDB (lokal auf Proxmox oder remote)
MONGO_URL=mongodb://localhost:27017
DB_NAME=stundenzettel

# Lokaler Speicher für PDFs (auf Proxmox!)
LOCAL_RECEIPTS_PATH=/var/stundenzettel/receipts

# Ollama auf GMKTec (lokales Netzwerk)
OLLAMA_BASE_URL=http://192.168.1.100:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=300

# JWT & Verschlüsselung
SECRET_KEY=<generiere-starkes-secret-min-32-zeichen>
ENCRYPTION_KEY=<generiere-encryption-key>

# CORS (Frontend-URL auf All-inkl)
CORS_ORIGINS=https://ihre-domain.de
```

**Option B: Docker auf Proxmox**

```bash
# Docker installieren
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Docker Compose installieren
sudo apt install docker-compose-plugin

# docker-compose.yml erstellen
```

**Systemd Service (für Option A):**

```ini
# /etc/systemd/system/stundenzettel-backend.service
[Unit]
Description=Stundenzettel Backend API
After=network.target mongod.service

[Service]
Type=simple
User=stundenzettel
WorkingDirectory=/opt/stundenzettel_web/backend
Environment="PATH=/opt/stundenzettel_web/backend/venv/bin"
EnvironmentFile=/opt/stundenzettel_web/backend/.env
ExecStart=/opt/stundenzettel_web/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**Service starten:**
```bash
sudo systemctl enable stundenzettel-backend
sudo systemctl start stundenzettel-backend
```

---

### 3. MongoDB → **Proxmox Server** (oder remote)

**Option A: MongoDB lokal auf Proxmox**

```bash
# MongoDB installieren
sudo apt install -y mongodb

# Oder Docker:
docker run -d --name mongodb \
  -p 27017:27017 \
  -v /var/lib/mongodb:/data/db \
  mongo:latest
```

**Option B: MongoDB Atlas (remote, Cloud)**

```env
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/stundenzettel?retryWrites=true&w=majority
```

---

### 4. Agents → **Proxmox Server** (läuft mit Backend zusammen!)

**⚠️ WICHTIG: Agents sind TEIL des Backends, kein separater Service!**

Die Agents (`backend/agents.py`) werden **direkt vom Backend aufgerufen**. Sie laufen **nicht** als separater Container oder Service.

**Wie es funktioniert:**
- Backend ruft `AgentOrchestrator` auf
- Agents laufen im gleichen Python-Prozess wie Backend
- Agents kommunizieren über HTTP mit Ollama auf GMKTec

**Keine separate Installation nötig!** Die Agents sind bereits im Backend-Code enthalten.

---

### 5. Ollama (LLM) → **GMKTec evo x2** (Home-Netzwerk)

**Was wird installiert:**
- Ollama Server
- LLM-Modelle (z.B. llama3.2)

**Installation auf GMKTec:**

```bash
# 1. Ollama installieren
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Ollama starten (als Service)
sudo systemctl enable ollama
sudo systemctl start ollama

# 3. Modell herunterladen
ollama pull llama3.2

# 4. Netzwerk-Zugriff konfigurieren
# Ollama hört standardmäßig auf 0.0.0.0:11434 (alle Interfaces)
# Falls Firewall aktiv: Port 11434 öffnen
sudo ufw allow from 192.168.1.0/24 to any port 11434
```

**Statische IP für GMKTec (empfohlen):**
- Router: DHCP-Reservierung für GMKTec MAC-Adresse
- Oder: Statische IP auf GMKTec selbst konfigurieren

**Test:**
```bash
# Von Proxmox aus testen
curl http://192.168.1.100:11434/api/tags
```

---

## 📋 Komplette Installations-Checkliste

### Phase 1: Proxmox vorbereiten

- [ ] Proxmox VM oder LXC Container erstellen (Ubuntu 22.04+)
- [ ] Python 3.11+ installieren
- [ ] MongoDB installieren (lokal oder remote konfigurieren)
- [ ] Verzeichnis für PDFs erstellen: `/var/stundenzettel/receipts`
- [ ] Firewall konfigurieren: Port 8000 für Backend öffnen

### Phase 2: Backend auf Proxmox installieren

- [ ] Projekt klonen: `git clone <repo> /opt/stundenzettel_web`
- [ ] Virtual Environment erstellen
- [ ] Dependencies installieren: `pip install -r requirements.txt`
- [ ] `.env` Datei erstellen mit:
  - MongoDB URL
  - LOCAL_RECEIPTS_PATH
  - OLLAMA_BASE_URL (GMKTec IP)
  - SECRET_KEY, ENCRYPTION_KEY
  - CORS_ORIGINS
- [ ] Systemd Service erstellen
- [ ] Backend starten: `sudo systemctl start stundenzettel-backend`
- [ ] Backend testen: `curl http://localhost:8000/health`

### Phase 3: GMKTec (Ollama) konfigurieren

- [ ] Ollama installieren
- [ ] Ollama als Service starten
- [ ] Modell herunterladen: `ollama pull llama3.2`
- [ ] Statische IP konfigurieren (empfohlen)
- [ ] Firewall: Port 11434 für Proxmox erlauben
- [ ] Test: Von Proxmox aus Ollama erreichen

### Phase 4: Frontend auf All-inkl installieren

- [ ] Frontend lokal bauen: `npm run build`
- [ ] `.env` vor Build: `REACT_APP_BACKEND_URL=https://proxmox-domain:8000`
- [ ] Inhalt von `frontend/build/` auf All-inkl hochladen
- [ ] `.htaccess` hochladen (für React Router)
- [ ] SSL/HTTPS auf All-inkl aktivieren

### Phase 5: Netzwerk & Sicherheit

- [ ] Nginx Reverse Proxy auf Proxmox (für HTTPS)
- [ ] SSL-Zertifikat (Let's Encrypt) für Proxmox
- [ ] Firewall-Regeln:
  - Proxmox: Port 8000 für All-inkl erlauben
  - GMKTec: Port 11434 für Proxmox erlauben
- [ ] CORS in Backend konfiguriert

### Phase 6: Test & Validierung

- [ ] Frontend lädt: `https://ihre-domain.de`
- [ ] Backend erreichbar: `https://proxmox-domain:8000/health`
- [ ] Login funktioniert
- [ ] Stundenzettel erstellen funktioniert
- [ ] PDF-Generierung funktioniert
- [ ] Reisekosten-App funktioniert
- [ ] Agents können Ollama erreichen (Test-Reisekosten-Prüfung)

---

## 🔧 Konfiguration im Detail

### Backend .env (auf Proxmox)

```env
# MongoDB
MONGO_URL=mongodb://localhost:27017
DB_NAME=stundenzettel

# Lokaler Speicher (auf Proxmox!)
LOCAL_RECEIPTS_PATH=/var/stundenzettel/receipts

# Ollama (GMKTec im Home-Netzwerk)
OLLAMA_BASE_URL=http://192.168.1.100:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=300
OLLAMA_MAX_RETRIES=3

# JWT & Security
SECRET_KEY=<generiere-mit-openssl-rand-hex-32>
ENCRYPTION_KEY=<generiere-mit-openssl-rand-hex-32>

# CORS (Frontend-URL auf All-inkl)
CORS_ORIGINS=https://ihre-domain.de,https://www.ihre-domain.de
```

### Frontend .env (vor Build)

```env
REACT_APP_BACKEND_URL=https://proxmox-domain.de:8000
```

### Nginx Reverse Proxy (auf Proxmox)

```nginx
server {
    listen 443 ssl http2;
    server_name proxmox-domain.de;

    ssl_certificate /etc/letsencrypt/live/proxmox-domain.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/proxmox-domain.de/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## ❌ Häufige Fehler vermeiden

### ❌ FALSCH: Backend auf All-inkl installieren

**Warum falsch:**
- All-inkl unterstützt kein Python/FastAPI
- Keine MongoDB möglich
- Keine lokale Dateispeicherung
- Agents können nicht laufen

### ❌ FALSCH: Agents als separaten Container laufen lassen

**Warum falsch:**
- Agents sind Teil des Backends
- Werden direkt vom Backend aufgerufen
- Kein separater Service nötig

### ✅ RICHTIG: Backend auf Proxmox

**Warum richtig:**
- Volle Kontrolle über Python-Umgebung
- MongoDB lokal möglich
- Lokale Dateispeicherung
- Agents laufen im Backend-Prozess

---

## 📊 Datenfluss

### Stundenzettel erstellen:
```
User (Browser) 
  → Frontend (All-inkl) 
  → Backend API (Proxmox:8000) 
  → MongoDB (Proxmox)
  → PDF-Generierung (Proxmox)
  → E-Mail-Versand (Proxmox)
```

### Reisekosten prüfen:
```
User (Browser)
  → Frontend (All-inkl)
  → Backend API (Proxmox:8000)
  → Agents (laufen im Backend-Prozess auf Proxmox)
  → Ollama API (GMKTec:11434) über lokales Netzwerk
  → Ergebnisse zurück
  → MongoDB Update (Proxmox)
```

### PDF-Upload:
```
User (Browser)
  → Frontend (All-inkl)
  → Backend API (Proxmox:8000)
  → Speicherung in /var/stundenzettel/receipts (Proxmox)
  → Verschlüsselung (Proxmox)
  → MongoDB Metadaten (Proxmox)
```

---

## 🎯 Zusammenfassung: Was wo installiert wird

| Komponente | Server | Technologie | Port | Öffentlich erreichbar? |
|------------|--------|-------------|------|----------------------|
| **Frontend** | All-inkl.com | React Build (statisch) | 443 (HTTPS) | ✅ Ja |
| **Backend API** | Proxmox | Python/FastAPI | 8000 | ✅ Ja (über HTTPS) |
| **MongoDB** | Proxmox | MongoDB | 27017 | ❌ Nein (nur lokal) |
| **Agents** | Proxmox | Python (im Backend) | - | ❌ Nein (lokal) |
| **Ollama** | GMKTec evo x2 | Ollama Server | 11434 | ❌ Nein (lokal) |
| **Local Storage** | Proxmox | Dateisystem | - | ❌ Nein (lokal) |

**Wichtig:**
- ✅ Frontend: All-inkl (nur statische Dateien)
- ✅ Backend: Proxmox (Python/FastAPI)
- ✅ Agents: Proxmox (laufen mit Backend zusammen)
- ✅ Ollama: GMKTec (Home-Netzwerk)
- ✅ MongoDB: Proxmox (oder remote)

**NICHT auf All-inkl:**
- ❌ Backend (Python wird nicht unterstützt)
- ❌ MongoDB
- ❌ Agents
- ❌ Lokale Dateispeicherung

---

## 📚 Weitere Dokumentation

- **Architektur-Details:** Siehe `ARCHITEKTUR_ALL_INKL_PROXMOX.md`
- **LLM-Integration:** Siehe `backend/LLM_INTEGRATION.md`
- **Agent-System:** Siehe `backend/AGENTS_README.md`

