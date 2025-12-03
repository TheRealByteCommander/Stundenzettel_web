# 🔄 Backend-Update-Anleitung

## Übersicht

Diese Anleitung zeigt, wie Sie das Backend nach Änderungen an der LLM-Konfiguration oder anderen Updates aktualisieren.

---

## 🐳 Option 1: Docker/Container-Deployment

### Wenn Sie Docker Compose verwenden:

```bash
# 1. In das Backend-Verzeichnis wechseln
cd /path/to/stundenzettel_web/backend

# 2. Änderungen aus dem Repository holen
git pull origin main

# 3. Container neu bauen und starten
docker compose -f docker-compose.agents.yml down
docker compose -f docker-compose.agents.yml build --no-cache
docker compose -f docker-compose.agents.yml up -d

# 4. Logs überprüfen
docker compose -f docker-compose.agents.yml logs -f agents
```

### Schnell-Update (ohne Rebuild):

```bash
# Nur Container neu starten (wenn nur Config geändert wurde)
docker compose -f docker-compose.agents.yml restart agents
```

---

## 🖥️ Option 2: Proxmox Container (LXC) - Direkte Installation

### Wenn Sie das Backend direkt auf einem Proxmox CT installiert haben:

```bash
# 1. SSH in den Backend-Container
ssh root@192.168.178.157  # Ihre Backend-IP

# 2. In das Projekt-Verzeichnis wechseln
cd /opt/stundenzettel_web/backend
# oder wo auch immer Sie das Projekt installiert haben

# 3. Änderungen aus dem Repository holen
git pull origin main

# 4. Python-Abhängigkeiten aktualisieren (falls nötig)
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 5. Service neu starten
sudo systemctl restart tick-guard-backend

# 6. Status überprüfen
sudo systemctl status tick-guard-backend
```

### Environment-Variablen aktualisieren:

```bash
# .env Datei bearbeiten
nano /opt/stundenzettel_web/backend/.env

# Folgende Werte sollten gesetzt sein:
# OLLAMA_BASE_URL=http://192.168.178.155:11434
# OLLAMA_MODEL_CHAT=Qwen2.5:32B
# OLLAMA_MODEL_DOCUMENT=Qwen2.5vl:7b
# OLLAMA_MODEL_ACCOUNTING=DeepSeek-R1:32B
# OLLAMA_TIMEOUT=600

# Service neu starten
sudo systemctl restart tick-guard-backend
```

---

## 🚀 Option 3: Automatisches Update-Script

Erstellen Sie ein Update-Script `update_backend.sh`:

```bash
#!/bin/bash
set -e

echo "🔄 Backend-Update wird durchgeführt..."

# Projekt-Verzeichnis (anpassen!)
PROJECT_DIR="/opt/stundenzettel_web/backend"
cd "$PROJECT_DIR"

# Git Pull
echo "📥 Änderungen werden geholt..."
git pull origin main

# Python-Abhängigkeiten aktualisieren
echo "📦 Abhängigkeiten werden aktualisiert..."
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Service neu starten
echo "🔄 Service wird neu gestartet..."
sudo systemctl restart tick-guard-backend

# Status anzeigen
echo "✅ Update abgeschlossen!"
sudo systemctl status tick-guard-backend --no-pager
```

**Verwendung:**
```bash
chmod +x update_backend.sh
sudo ./update_backend.sh
```

---

## 🔍 Option 4: Manuelle Python-Installation (Development)

### Wenn Sie das Backend lokal für Entwicklung laufen lassen:

```bash
# 1. In das Backend-Verzeichnis wechseln
cd backend

# 2. Änderungen holen
git pull origin main

# 3. Virtual Environment aktivieren
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows

# 4. Abhängigkeiten aktualisieren
pip install -r requirements.txt --upgrade

# 5. Server neu starten
# Stoppen Sie den laufenden Server (Ctrl+C) und starten Sie neu:
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

---

## ✅ Nach dem Update prüfen

### 1. Health Check

```bash
# Von Proxmox-Server
curl http://192.168.178.155:11434/api/tags

# Sollte JSON mit verfügbaren Modellen zurückgeben
```

### 2. Backend-Status prüfen

```bash
# Docker
docker compose -f docker-compose.agents.yml ps

# Systemd
sudo systemctl status tick-guard-backend
```

### 3. Logs überprüfen

```bash
# Docker
docker compose -f docker-compose.agents.yml logs -f agents

# Systemd
sudo journalctl -u tick-guard-backend -f
```

### 4. LLM-Verbindung testen

Die Agents sollten beim Start automatisch die LLM-Verfügbarkeit prüfen. In den Logs sollten Sie sehen:

```
✅ Ollama LLM erreichbar für ChatAgent: http://192.168.178.155:11434 (Modell: Qwen2.5:32B)
✅ Ollama LLM erreichbar für DocumentAgent: http://192.168.178.155:11434 (Modell: Qwen2.5vl:7b)
✅ Ollama LLM erreichbar für AccountingAgent: http://192.168.178.155:11434 (Modell: DeepSeek-R1:32B)
```

---

## ⚠️ Wichtige Hinweise

### 1. Environment-Variablen

Stellen Sie sicher, dass alle Environment-Variablen korrekt gesetzt sind:

```env
OLLAMA_BASE_URL=http://192.168.178.155:11434
OLLAMA_MODEL_CHAT=Qwen2.5:32B
OLLAMA_MODEL_DOCUMENT=Qwen2.5vl:7b
OLLAMA_MODEL_ACCOUNTING=DeepSeek-R1:32B
OLLAMA_TIMEOUT=600
```

### 2. Modelle auf GMKTec prüfen

Stellen Sie sicher, dass die Modelle auf dem GMKTec-Server verfügbar sind:

```bash
# Auf GMKTec evo x2
ollama list

# Sollte zeigen:
# Qwen2.5:32B
# Qwen2.5vl:7b
# DeepSeek-R1:32B
```

Falls Modelle fehlen:
```bash
ollama pull Qwen2.5:32B
ollama pull Qwen2.5vl:7b
ollama pull DeepSeek-R1:32B
```

### 3. Netzwerk-Verbindung

Testen Sie die Verbindung vom Backend-Server zum GMKTec:

```bash
# Vom Backend-Server
ping 192.168.178.155
curl http://192.168.178.155:11434/api/tags
```

---

## 🐛 Troubleshooting

### Problem: "Connection refused" zu Ollama

**Lösung:**
1. Prüfen Sie, ob Ollama auf GMKTec läuft:
   ```bash
   # Auf GMKTec
   systemctl status ollama
   ```

2. Prüfen Sie Firewall-Regeln:
   ```bash
   # Auf GMKTec
   sudo ufw allow from 192.168.178.0/24 to any port 11434
   ```

### Problem: "Model not found"

**Lösung:**
1. Prüfen Sie verfügbare Modelle:
   ```bash
   # Auf GMKTec
   ollama list
   ```

2. Laden Sie fehlende Modelle herunter:
   ```bash
   ollama pull Qwen2.5:32B
   ollama pull Qwen2.5vl:7b
   ollama pull DeepSeek-R1:32B
   ```

### Problem: Container startet nicht

**Lösung:**
```bash
# Logs ansehen
docker compose -f docker-compose.agents.yml logs agents

# Container neu bauen
docker compose -f docker-compose.agents.yml build --no-cache
docker compose -f docker-compose.agents.yml up -d
```

---

## 📝 Zusammenfassung

**Schnell-Update (Docker):**
```bash
cd backend && git pull && docker compose -f docker-compose.agents.yml restart agents
```

**Schnell-Update (Systemd):**
```bash
cd /opt/tick-guard/stundenzettel_web/backend && git pull && sudo systemctl restart tick-guard-backend
```

**Vollständiges Update (Docker):**
```bash
cd backend && git pull && docker compose -f docker-compose.agents.yml down && docker compose -f docker-compose.agents.yml build --no-cache && docker compose -f docker-compose.agents.yml up -d
```

---

**Update erfolgreich! 🎉**
