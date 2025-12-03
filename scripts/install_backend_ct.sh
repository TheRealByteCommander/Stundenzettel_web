#!/usr/bin/env bash
set -euo pipefail

log() { printf '[%(%Y-%m-%dT%H:%M:%S%z)T] [install-backend] %s\n' -1 "$*"; }
warn() { printf '[%(%Y-%m-%dT%H:%M:%S%z)T] [install-backend][WARN] %s\n' -1 "$*" >&2; }
abort() { printf '[%(%Y-%m-%dT%H:%M:%S%z)T] [install-backend][ERROR] %s\n' -1 "$*" >&2; exit 1; }

trap 'abort "Fehler (exit $?) bei Befehl \"${BASH_COMMAND}\" in Zeile ${LINENO}."' ERR

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  abort "Bitte als root bzw. mit sudo ausführen."
fi

umask 022

REPO_URL="${REPO_URL:-https://github.com/TheRealByteCommander/Stundenzettel_web.git}"
REPO_BRANCH="${REPO_BRANCH:-main}"
INSTALL_DIR="${INSTALL_DIR:-/opt/tick-guard}"
PROJECT_DIR="${PROJECT_DIR:-$INSTALL_DIR/Stundenzettel_web}"
BACKEND_DIR="$PROJECT_DIR/backend"
SERVICE_USER="${SERVICE_USER:-tickguard}"
SERVICE_NAME="${SERVICE_NAME:-tick-guard-backend}"
# Stelle sicher, dass RECEIPTS_PATH absolut ist
RECEIPTS_PATH="${LOCAL_RECEIPTS_PATH:-/var/tick-guard/receipts}"
# Konvertiere zu absolutem Pfad falls relativ
if [[ ! "$RECEIPTS_PATH" = /* ]]; then
  RECEIPTS_PATH="$(realpath -m "$RECEIPTS_PATH" 2>/dev/null || echo "/var/tick-guard/receipts")"
fi
FRONTEND_IP="${FRONTEND_IP:-192.168.178.156}"
BACKEND_IP="${BACKEND_IP:-192.168.178.157}"
OLLAMA_IP="${OLLAMA_IP:-192.168.178.155}"
DDNS_DOMAIN="${DDNS_DOMAIN:-${FRONTEND_IP}}"
OLLAMA_MODEL="${OLLAMA_MODEL:-Qwen2.5:32B}"
OLLAMA_MODEL_CHAT="${OLLAMA_MODEL_CHAT:-Qwen2.5:32B}"
OLLAMA_MODEL_DOCUMENT="${OLLAMA_MODEL_DOCUMENT:-Qwen2.5vl:7b}"
OLLAMA_MODEL_ACCOUNTING="${OLLAMA_MODEL_ACCOUNTING:-DeepSeek-R1:32B}"
OLLAMA_TIMEOUT="${OLLAMA_TIMEOUT:-600}"
CORS_ORIGINS="${CORS_ORIGINS:-http://$FRONTEND_IP}"
VAPID_PUBLIC_KEY="${VAPID_PUBLIC_KEY:-}"
VAPID_PRIVATE_KEY="${VAPID_PRIVATE_KEY:-}"
VAPID_CLAIM_EMAIL="${VAPID_CLAIM_EMAIL:-admin@$DDNS_DOMAIN}"
SECRET_KEY="${SECRET_KEY:-}"
ENCRYPTION_KEY="${ENCRYPTION_KEY:-}"

log "Installationsparameter:"
log "  Repository:        $REPO_URL (Branch: $REPO_BRANCH)"
log "  Installationspfad: $PROJECT_DIR"
log "  Backend-IP:        $BACKEND_IP"
log "  Frontend-IP:       $FRONTEND_IP"
log "  Ollama-IP:         $OLLAMA_IP"
log "  DDNS-Domain:       $DDNS_DOMAIN"

if [[ "$DDNS_DOMAIN" == "ddns.example.tld" ]]; then
  warn "DDNS_DOMAIN ist nicht gesetzt – Standardwert 'ddns.example.tld' wird verwendet."
fi

log "System aktualisieren und Basis-Konfiguration durchführen…"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y

# Zeitzone auf Europe/Berlin setzen (falls nicht bereits gesetzt)
if [[ -f /etc/timezone ]] && [[ "$(cat /etc/timezone)" != "Europe/Berlin" ]]; then
  log "Zeitzone auf Europe/Berlin setzen…"
  timedatectl set-timezone Europe/Berlin || warn "Zeitzone konnte nicht gesetzt werden."
fi

log "Pakete aktualisieren und Basis-Abhängigkeiten installieren…"

APT_BASE_PACKAGES=(
  python3
  python3-venv
  python3-pip
  git
  build-essential
  curl
  ufw
  openssl
  jq
  gnupg
  ca-certificates
)
log "Installiere Basis-Pakete: ${APT_BASE_PACKAGES[*]}"
apt-get install -y "${APT_BASE_PACKAGES[@]}"

# MongoDB installieren (Ubuntu 22.04)
log "MongoDB Repository hinzufügen und installieren…"
if ! command -v mongod >/dev/null 2>&1; then
  # MongoDB GPG Key hinzufügen
  curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg || \
    curl -fsSL https://pgp.mongodb.com/server-7.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg || \
    abort "MongoDB GPG Key konnte nicht heruntergeladen werden."
  
  # MongoDB Repository hinzufügen (Ubuntu 22.04 = jammy)
  echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
    tee /etc/apt/sources.list.d/mongodb-org-7.0.list || \
    abort "MongoDB Repository konnte nicht hinzugefügt werden."
  
  apt-get update -y
  apt-get install -y mongodb-org || warn "MongoDB konnte nicht installiert werden. Bitte manuell prüfen."
else
  log "MongoDB ist bereits installiert."
fi

if ! command -v openssl >/dev/null 2>&1; then
  abort "openssl ist nicht verfügbar – Schlüssel können nicht generiert werden."
fi

if [[ -z "$SECRET_KEY" ]]; then
  SECRET_KEY="$(openssl rand -hex 32)" || abort "SECRET_KEY konnte nicht erzeugt werden."
fi
if [[ -z "$ENCRYPTION_KEY" ]]; then
  ENCRYPTION_KEY="$(openssl rand -hex 32)" || abort "ENCRYPTION_KEY konnte nicht erzeugt werden."
fi

if systemctl list-unit-files | grep -q "^mongod\.service"; then
  systemctl enable --now mongod
elif systemctl list-unit-files | grep -q "^mongodb\.service"; then
  systemctl enable --now mongodb
else
  log "Hinweis: MongoDB-Dienst konnte nicht gefunden werden. Bitte ggf. manuell prüfen."
fi

if ! id -u "$SERVICE_USER" >/dev/null 2>&1; then
  log "Systembenutzer $SERVICE_USER anlegen…"
  useradd --system --home "$INSTALL_DIR" --shell /usr/sbin/nologin "$SERVICE_USER"
fi

log "Repository vorbereiten…"
mkdir -p "$INSTALL_DIR"
if [[ -d "$PROJECT_DIR/.git" ]]; then
  git -C "$PROJECT_DIR" fetch --all --prune
  git -C "$PROJECT_DIR" reset --hard "origin/$REPO_BRANCH"
else
  git clone --depth 1 --branch "$REPO_BRANCH" "$REPO_URL" "$PROJECT_DIR"
fi

chown -R "$SERVICE_USER":"$SERVICE_USER" "$INSTALL_DIR"

cd "$BACKEND_DIR"

if [[ ! -f requirements.txt ]]; then
  abort "Backend-Verzeichnis $BACKEND_DIR ist unvollständig (requirements.txt fehlt)."
fi

log "Python Virtualenv einrichten…"
if [[ ! -d venv ]]; then
  python3 -m venv venv
fi

# shellcheck disable=SC1091
source venv/bin/activate
pip install --upgrade pip wheel
pip install -r requirements.txt

# Optionale erweiterte Tools installieren (falls gewünscht)
log "Optionale erweiterte Agent-Tools prüfen…"

# Priorität 1 Tools
if [[ "${INSTALL_PRIO1_TOOLS:-false}" == "true" ]]; then
  log "Installiere Priorität 1 Tools…"
  pip install imagehash>=4.3.1 || warn "imagehash konnte nicht installiert werden (optional)"
  pip install opencv-python>=4.8.0 || warn "opencv-python konnte nicht installiert werden (optional)"
  pip install pytz>=2023.3 || warn "pytz konnte nicht installiert werden (optional)"
  pip install timezonefinder>=6.2.0 || warn "timezonefinder konnte nicht installiert werden (optional)"
  pip install dnspython>=2.4.0 || warn "dnspython konnte nicht installiert werden (optional)"
fi

# Priorität 2 Tools
if [[ "${INSTALL_PRIO2_TOOLS:-false}" == "true" ]]; then
  log "Installiere Priorität 2 Tools…"
  pip install imapclient>=2.3.1 || warn "imapclient konnte nicht installiert werden (optional)"
  pip install openpyxl>=3.1.0 || warn "openpyxl konnte nicht installiert werden (optional)"
  pip install phonenumbers>=8.13.0 || warn "phonenumbers konnte nicht installiert werden (optional)"
  # holidays ist bereits in requirements.txt
fi

# Priorität 3 Tools
if [[ "${INSTALL_PRIO3_TOOLS:-false}" == "true" ]]; then
  log "Installiere Priorität 3 Tools…"
  # pyzbar benötigt zbar (System-Paket)
  if ! command -v zbarimg >/dev/null 2>&1; then
    log "Installiere zbar (System-Paket für pyzbar)…"
    apt-get install -y libzbar0 zbar-tools || warn "zbar konnte nicht installiert werden (optional)"
  fi
  pip install pyzbar>=0.1.9 || warn "pyzbar konnte nicht installiert werden (optional)"
  # pillow für QR-Code/Barcode-Erkennung (falls nicht bereits installiert)
  pip install pillow>=10.0.0 || warn "pillow konnte nicht installiert werden (optional)"
  # opencv-python sollte bereits für Priorität 1 Tools installiert sein
fi

# Einzelne Tools (für gezielte Installation)
if [[ "${INSTALL_EXA_TOOL:-false}" == "true" ]]; then
  log "Installiere Exa/XNG Search Tool (exa-py)…"
  pip install exa-py || warn "Exa-Tool konnte nicht installiert werden (optional)"
fi

if [[ "${INSTALL_PADDLEOCR:-false}" == "true" ]]; then
  log "Installiere PaddleOCR (paddleocr, paddlepaddle)…"
  pip install paddleocr paddlepaddle || warn "PaddleOCR konnte nicht installiert werden (optional)"
fi

if [[ "${INSTALL_LANGCHAIN:-false}" == "true" ]]; then
  log "Installiere LangChain (langchain, langchain-openai)…"
  pip install langchain langchain-openai || warn "LangChain konnte nicht installiert werden (optional)"
fi

deactivate

log "Dateispeicher unter $RECEIPTS_PATH vorbereiten…"
mkdir -p "$RECEIPTS_PATH"
chown -R "$SERVICE_USER":"$SERVICE_USER" "$RECEIPTS_PATH"

ENV_FILE="$BACKEND_DIR/.env"
log ".env Datei schreiben ($ENV_FILE)…"
cat >"$ENV_FILE" <<EOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=stundenzettel
LOCAL_RECEIPTS_PATH=$RECEIPTS_PATH
SECRET_KEY=$SECRET_KEY
ENCRYPTION_KEY=$ENCRYPTION_KEY
OLLAMA_BASE_URL=http://$OLLAMA_IP:11434
OLLAMA_MODEL=$OLLAMA_MODEL
OLLAMA_MODEL_CHAT=$OLLAMA_MODEL_CHAT
OLLAMA_MODEL_DOCUMENT=$OLLAMA_MODEL_DOCUMENT
OLLAMA_MODEL_ACCOUNTING=$OLLAMA_MODEL_ACCOUNTING
OLLAMA_TIMEOUT=$OLLAMA_TIMEOUT
OLLAMA_MAX_RETRIES=3
CORS_ORIGINS=$CORS_ORIGINS
VAPID_PUBLIC_KEY=$VAPID_PUBLIC_KEY
VAPID_PRIVATE_KEY=$VAPID_PRIVATE_KEY
VAPID_CLAIM_EMAIL=$VAPID_CLAIM_EMAIL
# Optionale Agent-Tools (falls installiert)
# EXA_API_KEY=your_exa_api_key_here
# MARKER_API_KEY=your_marker_api_key_here
# MARKER_BASE_URL=https://api.marker.io/v1
# DEEPL_API_KEY=your_deepl_api_key_here (für TranslationTool - optional)
# WEATHER_API_KEY=your_weather_api_key_here (für WeatherAPITool - optional, OpenWeatherMap oder WeatherAPI)
# WEATHER_API_PROVIDER=openweathermap (Standard: openweathermap, alternativ: weatherapi)
# GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here (für TravelTimeCalculatorTool - optional)
# OPENROUTESERVICE_API_KEY=your_ors_api_key_here (für TravelTimeCalculatorTool - optional, kostenlos bei openrouteservice.org)
# WEB_ACCESS_ALLOWED_DOMAINS=example.com,api.example.com (optional, leer = alle erlaubt)
# WEB_ACCESS_BLOCKED_DOMAINS=localhost,127.0.0.1,0.0.0.0 (Standard)
EOF
chown "$SERVICE_USER":"$SERVICE_USER" "$ENV_FILE"

SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
log "Systemd Service (${SERVICE_FILE}) anlegen…"
cat >"$SERVICE_FILE" <<EOF
[Unit]
Description=Tick Guard Backend API
After=network-online.target mongod.service mongodb.service

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$BACKEND_DIR/venv/bin"
EnvironmentFile=$ENV_FILE
ExecStart=$BACKEND_DIR/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME"

log "UFW Regeln aktualisieren…"
if command -v ufw >/dev/null 2>&1; then
  ufw allow from "$FRONTEND_IP" to any port 8000 proto tcp >/dev/null 2>&1 || true
  ufw allow OpenSSH >/dev/null 2>&1 || true
  if ufw status | grep -q "inactive"; then
    ufw --force enable >/dev/null 2>&1 || true
  fi
else
  log "UFW nicht installiert – Firewall-Regeln bitte manuell prüfen."
fi

log "Backend-Service Status:"
systemctl status "$SERVICE_NAME" --no-pager || warn "Service $SERVICE_NAME konnte nicht geprüft werden."

log "Gesundheitscheck:"
if command -v curl >/dev/null 2>&1; then
  MAX_RETRIES=5
  RETRY_COUNT=0
  while [[ $RETRY_COUNT -lt $MAX_RETRIES ]]; do
    if curl -sSf http://localhost:8000/health >/dev/null; then
      log "✅ Health-Check erfolgreich."
      break
    else
      RETRY_COUNT=$((RETRY_COUNT + 1))
      if [[ $RETRY_COUNT -lt $MAX_RETRIES ]]; then
        log "Health-Check fehlgeschlagen - warte 3 Sekunden und versuche es erneut ($RETRY_COUNT/$MAX_RETRIES)..."
        sleep 3
      else
        warn "⚠️  Health-Check fehlgeschlagen nach $MAX_RETRIES Versuchen – bitte Logs (`journalctl -u $SERVICE_NAME`) prüfen."
      fi
    fi
  done
else
  warn "curl nicht verfügbar, Health-Check übersprungen."
fi

# Ollama-Verbindung testen
log "Ollama-Verbindung wird getestet..."
if command -v curl >/dev/null 2>&1; then
  if curl -sSf "http://$OLLAMA_IP:11434/api/tags" >/dev/null; then
    log "✅ Ollama erreichbar unter http://$OLLAMA_IP:11434"
  else
    warn "⚠️  Ollama nicht erreichbar unter http://$OLLAMA_IP:11434 - bitte Netzwerk und Firewall prüfen"
  fi
else
  warn "curl nicht verfügbar, Ollama-Check übersprungen."
fi

cat <<SUMMARY

Installation abgeschlossen.

Wichtige Pfade:
  Projektpfad:   $PROJECT_DIR
  Backend:       $BACKEND_DIR
  .env:          $ENV_FILE
  Receipts:      $RECEIPTS_PATH
  Service:       $SERVICE_FILE

Nächste Schritte:
  - Überprüfe die .env, ggf. VAPID- oder SMTP-Werte ergänzen.
  - Stelle sicher, dass Ollama unter http://$OLLAMA_IP:11434 erreichbar ist.
  - Prüfe die Modelle auf dem Ollama-Server: ollama list
  - Frontend-Container konfigurieren (install_frontend_ct.sh).
  
Optionale erweiterte Agent-Tools:
  - Priorität 1 Tools: INSTALL_PRIO1_TOOLS=true (imagehash, opencv-python, pytz, timezonefinder, dnspython)
  - Priorität 2 Tools: INSTALL_PRIO2_TOOLS=true (imapclient, openpyxl, phonenumbers)
  - Priorität 3 Tools: INSTALL_PRIO3_TOOLS=true (pyzbar, benötigt zbar System-Paket)
  - Exa/XNG Search: INSTALL_EXA_TOOL=true und EXA_API_KEY in .env setzen
  - PaddleOCR: INSTALL_PADDLEOCR=true (für OCR-Fallback)
  - LangChain: INSTALL_LANGCHAIN=true (für erweiterte Workflows)
  
  Beispiel für vollständige Installation aller Tools:
    INSTALL_PRIO1_TOOLS=true INSTALL_PRIO2_TOOLS=true INSTALL_PRIO3_TOOLS=true \\
    INSTALL_EXA_TOOL=true INSTALL_PADDLEOCR=true INSTALL_LANGCHAIN=true \\
    EXA_API_KEY=your_key ./install_backend_ct.sh
  - Marker: MARKER_API_KEY in .env setzen (für erweiterte Dokumentenanalyse)
  
Update-Script:
  - Für zukünftige Updates: sudo scripts/update_backend.sh

SUMMARY

