# 🏗️ Architektur: All-inkl Webserver + Proxmox + GMKTec

## ⚠️ WICHTIG: All-inkl.com vs. Proxmox

**Klarstellung:**
- ✅ **Frontend auf All-inkl.com**: Nur statische Dateien (React Build) - hier gelten All-inkl-Regeln
- ✅ **Backend auf Proxmox**: Komplett unabhängig - **KEINE All-inkl-Regeln relevant!**

**Was bedeutet das für Sie:**
- ❌ **Keine PHP-Limits auf Backend**: Backend ist Python/FastAPI auf Proxmox
- ❌ **Keine Upload-Limits auf Backend**: Backend läuft auf Proxmox
- ❌ **Keine Datenbank-Limits**: MongoDB auf Proxmox (oder remote)
- ❌ **Keine PHP-Extensions**: Backend ist Python, nicht PHP
- ✅ **Volle Kontrolle**: Auf Proxmox haben Sie volle Kontrolle über das Backend
- ✅ **Eigene Firewall**: Firewall-Regeln auf Proxmox, nicht All-inkl

**All-inkl-Regeln gelten NUR für:**
1. Frontend-Hosting (statische Dateien)
2. `.htaccess` Konfiguration (für React Router)
3. Einmaliger Frontend-Build-Upload

**Proxmox-Regeln gelten für:**
- Backend-API (FastAPI)
- MongoDB-Instanz
- Agent-Container
- Lokale Dateispeicherung
- Firewall-Regeln
- SSL/HTTPS-Zertifikate

---

## Ihre spezifische Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                     All-inkl.com Webserver                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Frontend (React Build)                             │   │
│  │  - Statische Dateien                                │   │
│  │  - Public Web-Access                                │   │
│  └───────────────────────┬─────────────────────────────┘   │
│                          │ HTTPS                            │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           │ API-Calls
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                    │
│  - Läuft: ??? (muss definiert werden)                      │
│  - REST API                                                │
│  - MongoDB Verbindung                                      │
└──────┬───────────────────────────────────────┬──────────────┘
       │                                       │
       │                                       │
       ▼                                       ▼
┌─────────────────────┐          ┌──────────────────────────┐
│   MongoDB           │          │  Proxmox Server          │
│  (Remote/Lokal)     │          │  ┌────────────────────┐  │
│                     │          │  │ Backend API?       │  │
│                     │          │  │ Agent Container    │  │
│                     │          │  │ Local Storage      │  │
│                     │          │  │ /data/receipts     │  │
│                     │          │  └──────────┬─────────┘  │
└─────────────────────┘          └─────────────┼────────────┘
                                               │ HTTP API
                                               │ (lokal)
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

## Architektur-Optionen

### Option A: Backend auf All-inkl (mit PHP) ⚠️ Aktuell nicht unterstützt

**Problem:** All-inkl.com unterstützt kein Python/FastAPI nativ.

### Option B: Backend auf Proxmox (Empfohlen) ✅

**Architektur:**
```
Frontend (All-inkl) → Backend (Proxmox) → MongoDB → Agents (Proxmox) → LLM (GMKTec)
   [Statische        [Python/FastAPI]  [Proxmox]   [Proxmox]         [GMKTec]
    Dateien]          [KEINE All-inkl   [KEINE      [KEINE            [KEINE
   [All-inkl-Regeln]  Regeln!]          All-inkl-   All-inkl-Regeln!] All-inkl-
                                       Regeln!]                        Regeln!]
                                                     ↓
                                              Local Storage (Proxmox)
                                              [KEINE All-inkl-Regeln!]
```

**Wie es funktioniert:**

1. **Frontend auf All-inkl:**
   - React Build wird auf All-inkl Webserver hochgeladen
   - Statische Dateien (HTML, CSS, JS)
   - `.env` Datei: `REACT_APP_BACKEND_URL=https://proxmox-ip-oder-domain:8000`

2. **Backend auf Proxmox:**
   - FastAPI läuft als Container/VM auf Proxmox
   - Port 8000 nach außen erreichbar (Firewall/Port-Forwarding)
   - `LOCAL_RECEIPTS_PATH=/data/receipts` (lokaler Proxmox-Pfad)

3. **Agents auf Proxmox:**
   - Docker Container oder Python-Prozess
   - Direkt im selben Netzwerk wie Backend
   - Kommuniziert über HTTP mit Ollama auf GMKTec

4. **GMKTec evo x2:**
   - Im lokalen Netzwerk (Home) des Proxmox
   - Ollama läuft auf Port 11434
   - Erreichbar über lokale IP (z.B. `192.168.1.100:11434`)

## Routing und Verbindungen

### 1. Frontend → Backend

**Von All-inkl zu Proxmox:**

```javascript
// frontend/.env
REACT_APP_BACKEND_URL=https://proxmox-domain.de:8000
// oder
REACT_APP_BACKEND_URL=https://proxmox-ip:8000
```

**Wichtig:**
- HTTPS erforderlich (CORS, Sicherheit)
- Firewall auf Proxmox: Port 8000 öffnen
- Reverse Proxy (Nginx) empfohlen für SSL/TLS

### 2. Backend → MongoDB

**Optionen:**

```env
# MongoDB auf Proxmox (lokal)
MONGO_URL=mongodb://localhost:27017

# MongoDB remote (Internet)
MONGO_URL=mongodb://mongodb-atlas-cluster.mongodb.net/...

# MongoDB auf separatem Server
MONGO_URL=mongodb://mongodb-server:27017
```

### 3. Backend → Local Storage (Proxmox)

**Direkter Dateisystem-Zugriff:**

```env
# backend/.env (auf Proxmox)
LOCAL_RECEIPTS_PATH=/data/receipts
```

**Pfad auf Proxmox:**
- Container: `/data/receipts` (gemountet vom Host)
- Direkt auf Host: `/var/stundenzettel/receipts`

**Docker Volume Mount:**
```yaml
# docker-compose.yml (auf Proxmox)
volumes:
  - /var/stundenzettel/receipts:/data/receipts:rw
```

### 4. Backend → Agents (Proxmox)

**Lokale Kommunikation:**

```python
# backend/server.py
from agents import AgentOrchestrator

# Agents laufen lokal (gleicher Server)
orchestrator = AgentOrchestrator()
await orchestrator.review_expense_report(report_id, db)
```

**Kein Netzwerk-Overhead** - alles lokal!

### 5. Agents → Ollama (GMKTec)

**Lokales Netzwerk (Home):**

```env
# backend/.env (auf Proxmox)
OLLAMA_BASE_URL=http://192.168.1.100:11434
```

**Konfiguration:**
- GMKTec muss im gleichen Netzwerk wie Proxmox sein
- IP kann sich ändern (siehe Lösungen unten)
- Firewall auf GMKTec: Port 11434 für Proxmox-IP erlauben

## Lösung für dynamische GMKTec-IP

### Problem: GMKTec hat keine feste IP

### Lösung 1: Statische IP konfigurieren (Empfohlen)

**Auf Router oder GMKTec selbst:**

1. **Router DHCP-Reservation:**
   - Router-Admin → DHCP-Reservierungen
   - MAC-Adresse von GMKTec eintragen
   - Statische IP zuweisen (z.B. `192.168.1.100`)

2. **GMKTec statische IP manuell:**
   ```bash
   # Auf GMKTec (Linux)
   sudo nano /etc/netplan/50-cloud-init.yaml
   
   # Oder bei Ubuntu/Debian:
   sudo nano /etc/network/interfaces
   
   # Statische IP eintragen
   ```

### Lösung 2: Hostname verwenden (mDNS)

**Wenn mDNS/Bonjour aktiviert ist:**

```env
# backend/.env (auf Proxmox)
OLLAMA_BASE_URL=http://gmktec.local:11434
```

**Voraussetzungen:**
- mDNS auf GMKTec aktiviert
- Avahi/Bonjour installiert
- Im gleichen lokalen Netzwerk

### Lösung 3: DNS-Eintrag (falls DNS-Server vorhanden)

**DNS-A-Record:**
- `gmktec` → Aktuelle IP
- TTL: Niedrig (für häufige Updates)

```env
OLLAMA_BASE_URL=http://gmktec:11434
```

### Lösung 4: Health Check mit Auto-Discovery

**Optional: Backend kann GMKTec automatisch finden:**

```python
# Pseudo-Code für Auto-Discovery
async def find_ollama_server():
    # Scanne lokales Netzwerk nach Ollama
    for ip in local_network_range:
        try:
            response = await check_ollama(ip)
            if response:
                return f"http://{ip}:11434"
        except:
            continue
    return None
```

## Konfiguration Schritt für Schritt

### Schritt 1: Proxmox vorbereiten

```bash
# Auf Proxmox
# 1. Verzeichnis für Receipts erstellen
mkdir -p /var/stundenzettel/receipts
chmod 755 /var/stundenzettel/receipts

# 2. MongoDB installieren (oder remote verwenden)
# 3. Python/FastAPI Setup (oder Docker)
```

### Schritt 2: Backend auf Proxmox konfigurieren

```env
# backend/.env (auf Proxmox)
MONGO_URL=mongodb://localhost:27017
DB_NAME=stundenzettel

# Lokaler Speicher (Proxmox-Dateisystem)
LOCAL_RECEIPTS_PATH=/var/stundenzettel/receipts

# Ollama auf GMKTec (lokales Netzwerk)
OLLAMA_BASE_URL=http://192.168.1.100:11434
OLLAMA_MODEL=llama3.2

# Verschlüsselung
ENCRYPTION_KEY=...
SECRET_KEY=...
```

### Schritt 3: Frontend auf All-inkl konfigurieren

```env
# frontend/.env (für Build)
REACT_APP_BACKEND_URL=https://proxmox-domain.de:8000
```

**Build:**
```bash
npm run build
# Upload build/ Ordner nach All-inkl
```

### Schritt 4: Firewall/Netzwerk konfigurieren

**Proxmox Firewall:**
```bash
# Port 8000 für Backend-API öffnen
ufw allow 8000/tcp

# Oder für spezifische IPs (All-inkl Server)
ufw allow from ALL_INKL_IP to any port 8000
```

**GMKTec Firewall:**
```bash
# Port 11434 für Proxmox erlauben
ufw allow from PROXMOX_IP to any port 11434
```

### Schritt 5: Reverse Proxy (Nginx) auf Proxmox

**Für HTTPS und Domain:**

```nginx
# /etc/nginx/sites-available/stundenzettel
server {
    listen 443 ssl;
    server_name proxmox-domain.de;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Datenfluss

### Upload Reisekosten-Beleg

```
1. User (Browser) → Frontend (All-inkl)
2. Frontend → Backend API (Proxmox:8000)
3. Backend → Speichert PDF in /var/stundenzettel/receipts
4. Backend → Verschlüsselt Datei (DSGVO)
5. Backend → Speichert Metadaten in MongoDB
6. Backend → Antwort an Frontend
```

### Reisekosten-Prüfung

```
1. User → "Abrechnung abschließen"
2. Frontend → Backend API (Proxmox)
3. Backend → Agents aufrufen (lokal)
4. Agents → Ollama API (GMKTec:11434)
5. Ollama → Analysiert Dokumente
6. Agents → Ergebnisse zurück an Backend
7. Backend → MongoDB Update
8. Frontend → Benachrichtigung User
```

## Sicherheit

### Netzwerk-Sicherheit

1. **HTTPS für Frontend-Backend:**
   - SSL/TLS Zertifikat (Let's Encrypt)
   - Reverse Proxy auf Proxmox

2. **Firewall-Regeln:**
   - Nur benötigte Ports öffnen
   - Proxmox: Port 8000 nur für All-inkl
   - GMKTec: Port 11434 nur für Proxmox

3. **VPN für GMKTec (Optional):**
   - Wenn GMKTec nicht im gleichen Netzwerk
   - WireGuard oder OpenVPN

### DSGVO-Compliance

1. **Lokale Speicherung:**
   - Dateien nur auf Proxmox (nicht All-inkl)
   - Verschlüsselt gespeichert

2. **Audit-Logging:**
   - Alle Zugriffe werden protokolliert
   - Logs auf Proxmox gespeichert

3. **Verschlüsselung:**
   - Automatische Verschlüsselung aller PDFs
   - Schlüssel sicher gespeichert

## Troubleshooting

### Problem: Frontend kann Backend nicht erreichen

**Lösung:**
1. Firewall prüfen (Port 8000)
2. Backend läuft? `curl http://proxmox-ip:8000/health`
3. CORS-Konfiguration prüfen

### Problem: Backend kann Ollama nicht erreichen

**Lösung:**
1. GMKTec IP prüfen: `ping 192.168.1.100`
2. Ollama läuft? `curl http://192.168.1.100:11434/api/tags`
3. Firewall auf GMKTec prüfen

### Problem: Dateien werden nicht gespeichert

**Lösung:**
1. Berechtigungen prüfen: `ls -la /var/stundenzettel/receipts`
2. `LOCAL_RECEIPTS_PATH` korrekt?
3. Disk-Space prüfen: `df -h`

## Zusammenfassung

**Ihre Architektur:**

1. **Frontend:** All-inkl.com Webserver (statische Dateien)
2. **Backend:** Proxmox Server (FastAPI, Port 8000)
3. **MongoDB:** Auf Proxmox oder remote
4. **Agents:** Proxmox (Container/VM, lokal)
5. **Local Storage:** Proxmox Dateisystem (`/var/stundenzettel/receipts`)
6. **LLM (Ollama):** GMKTec evo x2 (Home-Netzwerk, Port 11434)

**Konfiguration:**

- **Frontend Build `.env`:** `REACT_APP_BACKEND_URL=https://proxmox-domain:8000`
  - Vor `npm run build` setzen
  - In Build integriert (statisch)
- **Backend `.env` (auf Proxmox):** `LOCAL_RECEIPTS_PATH=/var/stundenzettel/receipts`
- **Backend `.env` (auf Proxmox):** `OLLAMA_BASE_URL=http://192.168.1.100:11434` (statische IP empfohlen)

**Keine Netzwerk-Routing-Probleme!**
- ✅ Backend und Agents sind lokal auf Proxmox
- ✅ Dateispeicherung ist lokal (kein Netzwerk nötig)
- ✅ Nur Ollama-Aufrufe gehen über Netzwerk (lokal, Home-Netzwerk)
- ✅ Frontend → Backend über Internet (HTTPS)

**Wichtig:** 
- Proxmox Backend muss öffentlich erreichbar sein (oder VPN)
- Firewall: Port 8000 für All-inkl öffnen
- HTTPS empfohlen (Nginx Reverse Proxy mit Let's Encrypt)

