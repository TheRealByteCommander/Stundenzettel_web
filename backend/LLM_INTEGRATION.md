# 🤖 LLM-Integration für Proxmox Deployment

## Übersicht

Die Agenten laufen auf einem **Proxmox-Server** und kommunizieren über das lokale Netzwerk mit den LLMs, die auf einem **GMKTec evo x2** Rechner laufen.

## Architektur

```
┌─────────────────────┐
│   Proxmox Server    │
│  ┌───────────────┐  │
│  │ Agent Container│  │
│  │  (agents.py)   │  │
│  └───────┬───────┘  │
└──────────┼──────────┘
           │ HTTP/API
           │ (Port 11434)
           │
           ▼
┌─────────────────────┐
│  GMKTec evo x2      │
│  ┌───────────────┐  │
│  │ Ollama Server │  │
│  │  (localhost:  │  │
│  │   11434)      │  │
│  └───────────────┘  │
└─────────────────────┘
```

## Konfiguration

### 1. Ollama auf GMKTec evo x2 installieren

```bash
# Auf GMKTec evo x2 Rechner
curl -fsSL https://ollama.ai/install.sh | sh

# Ollama starten
ollama serve

# Modell herunterladen (z.B. llama3.2)
ollama pull llama3.2

# Alternative: Größere Modelle für bessere Qualität
ollama pull llama3.1:8b
ollama pull mistral:7b
```

### 2. Netzwerk-Zugriff konfigurieren

#### Auf GMKTec evo x2 (Ollama-Server)

Standardmäßig hört Ollama nur auf `localhost`. Für Netzwerk-Zugriff:

**Option A: Ollama standardmäßig auf allen Interfaces starten**

Ollama hört standardmäßig auf `0.0.0.0:11434`, also sollten Sie von anderen Rechnern im Netzwerk zugreifen können.

**Option B: Firewall-Regel erstellen (falls notwendig)**

```bash
# UFW (Ubuntu/Debian)
sudo ufw allow from 192.168.1.0/24 to any port 11434

# Firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="192.168.1.0/24" port protocol="tcp" port="11434" accept'
sudo firewall-cmd --reload
```

### 3. IP-Adresse des GMKTec-Servers ermitteln

```bash
# Auf GMKTec evo x2
ip addr show
# oder
hostname -I
```

Notieren Sie sich die IP-Adresse (z.B. `192.168.1.100`).

### 4. Environment-Variablen konfigurieren

#### Für direkte Python-Ausführung

Erstellen Sie `.env` Datei in `backend/`:

```bash
# .env
OLLAMA_BASE_URL=http://192.168.1.100:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=300
OLLAMA_MAX_RETRIES=3
OLLAMA_RETRY_DELAY=2.0
```

#### Für Docker/Proxmox Container

In `docker-compose.agents.yml` oder `.env`:

```yaml
environment:
  - OLLAMA_BASE_URL=http://192.168.1.100:11434
  - OLLAMA_MODEL=llama3.2
```

## Proxmox Deployment

### Option 1: LXC Container

1. **Container erstellen:**
   ```bash
   # Im Proxmox Web-Interface oder CLI
   pct create 100 ubuntu-22.04-standard \
     --hostname agents \
     --memory 2048 \
     --cores 2 \
     --net0 name=eth0,bridge=vmbr0,ip=dhcp
   ```

2. **Container starten:**
   ```bash
   pct start 100
   pct enter 100
   ```

3. **Python & Dependencies installieren:**
   ```bash
   apt update
   apt install python3.11 python3-pip python3-venv
   ```

4. **Application installieren:**
   ```bash
   cd /opt
   git clone <repository>
   cd stundenzettel_web/backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Systemd Service erstellen:**
   ```bash
   # /etc/systemd/system/agents.service
   [Unit]
   Description=Stundenzettel Agents
   After=network.target

   [Service]
   Type=simple
   User=agentuser
   WorkingDirectory=/opt/stundenzettel_web/backend
   Environment="PATH=/opt/stundenzettel_web/backend/venv/bin"
   EnvironmentFile=/opt/stundenzettel_web/backend/.env
   ExecStart=/opt/stundenzettel_web/backend/venv/bin/python3 -c "from agents import AgentOrchestrator; import asyncio; asyncio.run(...)"
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

### Option 2: Docker Container in Proxmox VM

1. **VM erstellen** (Ubuntu/Debian Server)

2. **Docker installieren:**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   ```

3. **Docker Compose installieren:**
   ```bash
   apt install docker-compose-plugin
   ```

4. **Container starten:**
   ```bash
   cd /opt/stundenzettel_web/backend
   docker compose -f docker-compose.agents.yml up -d
   ```

## Verbindung testen

### 1. Von Proxmox-Server zu GMKTec-Server

```bash
# Von Proxmox (Agent-Server)
curl http://192.168.1.100:11434/api/tags

# Sollte JSON mit verfügbaren Modellen zurückgeben:
# {"models": [{"name": "llama3.2", ...}]}
```

### 2. Health Check im Code

```python
from agents import OllamaLLM

llm = OllamaLLM(base_url="http://192.168.1.100:11434")
is_healthy = await llm.health_check()
print(f"Ollama erreichbar: {is_healthy}")
```

### 3. Test-Chat

```python
from agents import OllamaLLM

llm = OllamaLLM(base_url="http://192.168.1.100:11434", model="llama3.2")
response = await llm.chat([
    {"role": "user", "content": "Hallo, kannst du mich hören?"}
])
print(response)
```

## Netzwerk-Troubleshooting

### Problem: "Connection refused"

**Lösung:**
1. Überprüfen Sie, ob Ollama auf GMKTec läuft:
   ```bash
   # Auf GMKTec
   systemctl status ollama
   # oder
   ps aux | grep ollama
   ```

2. Testen Sie lokalen Zugriff:
   ```bash
   # Auf GMKTec
   curl http://localhost:11434/api/tags
   ```

3. Überprüfen Sie Firewall:
   ```bash
   # Auf GMKTec
   sudo ufw status
   sudo iptables -L -n | grep 11434
   ```

### Problem: "Timeout"

**Lösung:**
1. Erhöhen Sie `OLLAMA_TIMEOUT` in `.env`
2. Überprüfen Sie Netzwerk-Latenz:
   ```bash
   ping 192.168.1.100
   ```

### Problem: "Model not found"

**Lösung:**
1. Überprüfen Sie verfügbare Modelle:
   ```bash
   # Auf GMKTec
   ollama list
   ```

2. Passen Sie `OLLAMA_MODEL` in `.env` an

## Performance-Optimierung

### 1. Connection Pooling

Die `OllamaLLM` Klasse verwendet bereits Connection Pooling für bessere Performance bei mehreren Anfragen.

### 2. Timeout-Konfiguration

```bash
# Für schnelle Antworten (kleinere Modelle)
OLLAMA_TIMEOUT=60

# Für komplexe Analysen (größere Modelle)
OLLAMA_TIMEOUT=600
```

### 3. Retry-Logik

```bash
# Mehr Retries bei instabilem Netzwerk
OLLAMA_MAX_RETRIES=5
OLLAMA_RETRY_DELAY=3.0
```

## Sicherheit

### 1. Firewall-Regeln

Beschränken Sie Zugriff auf Ollama nur auf Proxmox-Server:

```bash
# Auf GMKTec (UFW)
sudo ufw allow from 192.168.1.50 to any port 11434  # Proxmox IP
sudo ufw deny 11434  # Alle anderen blockieren
```

### 2. VPN (Optional)

Für zusätzliche Sicherheit können Sie ein VPN zwischen Proxmox und GMKTec einrichten.

## Monitoring

### 1. Logs überwachen

```bash
# Agent-Logs
tail -f /var/log/agents.log

# Ollama-Logs (auf GMKTec)
journalctl -u ollama -f
```

### 2. Health Checks

```bash
# Regelmäßiger Health Check
*/5 * * * * curl -f http://192.168.1.100:11434/api/tags || echo "Ollama down" | mail -s "Alert" admin@example.com
```

## Modell-Empfehlungen

| Modell | Größe | RAM | Geschwindigkeit | Qualität |
|--------|-------|-----|-----------------|----------|
| llama3.2 | 2B | ~4GB | ⚡⚡⚡ | ⭐⭐ |
| llama3.1:8b | 8B | ~10GB | ⚡⚡ | ⭐⭐⭐ |
| mistral:7b | 7B | ~10GB | ⚡⚡ | ⭐⭐⭐⭐ |
| llama3:70b | 70B | ~80GB | ⚡ | ⭐⭐⭐⭐⭐ |

**Empfehlung:** `llama3.1:8b` oder `mistral:7b` für gute Balance zwischen Qualität und Performance.

## Nächste Schritte

1. ✅ Ollama auf GMKTec installieren
2. ✅ Netzwerk-Zugriff testen
3. ✅ Environment-Variablen konfigurieren
4. ✅ Agents auf Proxmox deployen
5. ✅ Health Check einrichten
6. ✅ Monitoring konfigurieren

---

**LLM-Integration erfolgreich konfiguriert! 🎉**

