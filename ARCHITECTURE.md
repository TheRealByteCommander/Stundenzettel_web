# 🏗️ System-Architektur

## Übersicht

Das Stundenzettel Web-System besteht aus mehreren Komponenten, die zusammenarbeiten:

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                        │
│  - Mobile-First Responsive Design                           │
│  - PWA-Support (Service Worker)                             │
│  - Sicherheits-Features (XSS, Rate Limiting)                │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend API (FastAPI/Python)                   │
│  - REST API                                                 │
│  - JWT Authentication + 2FA                                 │
│  - PDF-Generierung                                          │
│  - E-Mail-Versand                                           │
└──────┬──────────────────────────────────┬───────────────────┘
       │                                  │
       ▼                                  ▼
┌──────────────────┐          ┌──────────────────────────┐
│   MongoDB        │          │  Agent-System (Proxmox)  │
│  - Users         │          │  ┌────────────────────┐  │
│  - Timesheets    │          │  │ ChatAgent          │  │
│  - Travel        │          │  │ DocumentAgent      │  │
│  - Reports       │          │  │ AccountingAgent    │  │
│  - Announcements │          │  │ AgentOrchestrator  │  │
└──────────────────┘          │  └──────────┬─────────┘  │
                              └─────────────┼────────────┘
                                            │ HTTP API
                                            ▼
                              ┌──────────────────────────┐
                              │  Ollama LLM (GMKTec)     │
                              │  - llama3.2              │
                              │  - Andere Modelle        │
                              │  - Port 11434            │
                              └──────────────────────────┘
```

## Komponenten im Detail

### 1. Frontend (React)

**Technologie-Stack:**
- React 18+
- Tailwind CSS (Mobile-First)
- Axios für API-Kommunikation
- DOMPurify für XSS-Schutz
- Service Worker für PWA

**Features:**
- Responsive Design (Mobile-First)
- PWA-Support (Installierbar auf Mobilgeräten)
- Touch-optimierte UI
- Sicherheits-Features (Rate Limiting, Input Validation)

**Dateien:**
- `frontend/src/App.js` - Hauptkomponente
- `frontend/src/utils/security.js` - Sicherheits-Utilities
- `frontend/public/manifest.json` - PWA Manifest
- `frontend/public/sw.js` - Service Worker

### 2. Backend API (FastAPI)

**Technologie-Stack:**
- FastAPI (Python 3.11+)
- Motor (Async MongoDB Driver)
- JWT für Authentication
- PyOTP für 2FA
- ReportLab für PDF-Generierung

**Features:**
- REST API
- JWT-basierte Authentifizierung
- Obligatorische 2FA
- Rollenbasierte Zugriffskontrolle (User, Admin, Accounting)
- PDF-Generierung
- E-Mail-Versand (SMTP)

**Dateien:**
- `backend/server.py` - Haupt-API-Server
- `backend/compliance.py` - DSGVO-Compliance-Module
- `backend/agents.py` - Agent-Netzwerk
- `backend/migration_tool.py` - Migrations-Tool

### 3. Datenbank (MongoDB)

**Collections:**
- `users` - Benutzer (mit Rollen, 2FA, Wochenstunden)
- `weekly_timesheets` - Stundenzettel
- `travel_expense_reports` - Reisekostenabrechnungen
- `travel_expenses` - Einzelne Reisekosten
- `announcements` - Ankündigungen
- `chat_messages` - Chat-Nachrichten (Agent ↔ User)
- `smtp_config` - SMTP-Konfiguration

**DSGVO-Compliance:**
- Verschlüsselung sensibler Daten
- Audit-Logging
- Retention-Management

### 4. Agent-System

**Architektur:**
- **Proxmox-Server**: Agents laufen als Container/VM
- **GMKTec evo x2**: Ollama LLM-Server im lokalen Netzwerk

**Agenten:**
1. **ChatAgent**: Dialog mit Benutzer, Rückfragen
2. **DocumentAgent**: PDF-Analyse, OCR, Validierung
3. **AccountingAgent**: Zuordnung, Verpflegungsmehraufwand
4. **AgentOrchestrator**: Orchestrierung des Workflows

**Kommunikation:**
- HTTP API zwischen Proxmox und GMKTec
- Message Bus für Inter-Agent-Kommunikation
- Health Checks vor Verwendung

**Dateien:**
- `backend/agents.py` - Agent-Implementierung
- `backend/prompts/` - Markdown-Prompts für Agenten
- `backend/LLM_INTEGRATION.md` - Setup-Anleitung

### 5. LLM-Server (Ollama auf GMKTec)

**Setup:**
- Ollama installiert auf GMKTec evo x2
- Port 11434 (Standard)
- Zugriff über lokales Netzwerk (z.B. 192.168.1.100:11434)

**Konfiguration:**
```env
OLLAMA_BASE_URL=http://192.168.1.100:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=300
OLLAMA_MAX_RETRIES=3
```

**Features:**
- Connection Pooling
- Automatische Retries
- Timeout-Handling
- Health Checks

## Datenfluss

### Stundenzettel-Erstellung

```
User → Frontend → Backend API → MongoDB
                        ↓
                  PDF-Generierung
                        ↓
                  E-Mail-Versand
```

### Reisekosten-Prüfung

```
User → Frontend → Backend API → MongoDB
                        ↓
                  Agent-System (Proxmox)
                        ↓
                  Ollama LLM (GMKTec)
                        ↓
                  Dokumentenanalyse
                        ↓
                  Buchhaltungszuordnung
                        ↓
                  Chat bei Rückfragen
                        ↓
                  MongoDB (Update Report)
```

### Migration

```
Vorgänger-DB (Read-Only) → Migration-Tool → Neue MongoDB
                                      ↓
                              Mapping-Konfiguration
                                      ↓
                              Validierung
```

## Deployment-Szenarien

### Szenario 1: All-inkl.com (Shared Hosting)

```
Frontend (React Build) → All-inkl Webserver
Backend (PHP) → All-inkl Webserver
Datenbank (MySQL) → All-inkl MySQL
```

**Besonderheiten:**
- PHP statt Python
- MySQL statt MongoDB
- Keine LLM-Agents (Optional: Separate Server)

### Szenario 2: VPS/Cloud (Produktiv)

```
Frontend (React Build) → Nginx/CDN
Backend (Python/FastAPI) → VPS (Docker/Systemd)
Datenbank (MongoDB) → VPS/Managed MongoDB
Agent-System → Proxmox (Container/VM)
LLM-Server → GMKTec evo x2 (lokal)
```

### Szenario 3: Entwicklung

```
Frontend → npm start (localhost:3000)
Backend → uvicorn server:app (localhost:8000)
Datenbank → MongoDB (localhost:27017)
Agent-System → Lokal (Python)
LLM-Server → Ollama (localhost:11434)
```

### Szenario 4: Office-Rechner mit lokaler Speicherung

```
Frontend → Webserver (öffentlich)
Backend → Office-Rechner (lokal, über VPN/Reverse Tunnel)
Datenbank → MongoDB (remote oder lokal)
Lokale Dateien → Office-Rechner (C:/Reisekosten_Belege)
Agent-System → Proxmox (optional)
LLM-Server → GMKTec evo x2 (optional)
```

**Besonderheiten:**
- Backend läuft direkt auf Office-Rechner (DSGVO-konform)
- `LOCAL_RECEIPTS_PATH` zeigt auf lokales Laufwerk
- Keine Netzwerk-Freigabe nötig
- API erreichbar über VPN oder Reverse Tunnel

## Sicherheit

### Frontend
- XSS-Schutz (DOMPurify)
- Input-Validierung
- Rate Limiting
- Sichere Token-Speicherung (sessionStorage)

### Backend
- JWT Authentication
- 2FA (PyOTP)
- Password Hashing (bcrypt)
- CORS-Konfiguration
- Input-Validierung (Pydantic)

### DSGVO-Compliance
- Datenverschlüsselung (Fernet/AES-128)
- Audit-Logging
- Retention-Management
- Lokale Speichervalidierung
- AI-Transparenz (EU-AI-Act)

## Skalierung

### Horizontale Skalierung
- Backend: Mehrere Instanzen hinter Load Balancer
- MongoDB: Replica Set
- Agents: Mehrere Container auf Proxmox

### Vertikale Skalierung
- LLM-Server: Mehr RAM für größere Modelle
- MongoDB: Mehr RAM für größere Datasets
- Agents: Mehr CPU für parallele Verarbeitung

## Monitoring

### Logs
- Backend: Python Logging
- Agents: Structured Logging
- Frontend: Browser Console

### Health Checks
- Backend: `/health` Endpoint
- Agents: Ollama Health Check
- MongoDB: Connection Check

## Backup-Strategie

### Datenbank
- MongoDB: Automatische Backups (MongoDB Atlas oder lokale Scripts)
- MySQL: mysqldump (für All-inkl)

### Lokale Dateien
- Receipts: Lokale Backups auf Office-Rechner
- Verschlüsselt (DSGVO-konform)

## Weitere Dokumentation

- [LLM_INTEGRATION.md](backend/LLM_INTEGRATION.md) - LLM-Setup
- [DSGVO_COMPLIANCE.md](backend/DSGVO_COMPLIANCE.md) - Compliance
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Datenbank-Migration
- [INSTALLATION_COMPLETE.md](INSTALLATION_COMPLETE.md) - Installation

