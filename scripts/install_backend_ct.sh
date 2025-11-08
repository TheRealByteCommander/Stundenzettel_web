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
RECEIPTS_PATH="${LOCAL_RECEIPTS_PATH:-/var/tick-guard/receipts}"
FRONTEND_IP="${FRONTEND_IP:-192.168.178.150}"
BACKEND_IP="${BACKEND_IP:-192.168.178.151}"
OLLAMA_IP="${OLLAMA_IP:-192.168.178.155}"
DDNS_DOMAIN="${DDNS_DOMAIN:-ddns.example.tld}"
OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.2}"
OLLAMA_MODEL_CHAT="${OLLAMA_MODEL_CHAT:-$OLLAMA_MODEL}"
OLLAMA_MODEL_DOCUMENT="${OLLAMA_MODEL_DOCUMENT:-mistral-nemo}"
OLLAMA_MODEL_ACCOUNTING="${OLLAMA_MODEL_ACCOUNTING:-llama3.1}"
CORS_ORIGINS="${CORS_ORIGINS:-https://$DDNS_DOMAIN}"
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

log "Pakete aktualisieren und Basis-Abhängigkeiten installieren…"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y

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
)
log "Installiere Basis-Pakete: ${APT_BASE_PACKAGES[*]}"
apt-get install -y "${APT_BASE_PACKAGES[@]}"

if ! apt-get install -y mongodb; then
  warn "Paket 'mongodb' konnte nicht installiert werden. Bitte MongoDB manuell bereitstellen."
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
OLLAMA_TIMEOUT=300
OLLAMA_MAX_RETRIES=3
CORS_ORIGINS=$CORS_ORIGINS
VAPID_PUBLIC_KEY=$VAPID_PUBLIC_KEY
VAPID_PRIVATE_KEY=$VAPID_PRIVATE_KEY
VAPID_CLAIM_EMAIL=$VAPID_CLAIM_EMAIL
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
  if curl -sSf http://localhost:8000/health >/dev/null; then
    log "Health-Check erfolgreich."
  else
    warn "Health-Check fehlgeschlagen – bitte Logs (`journalctl -u $SERVICE_NAME`) prüfen."
  fi
else
  warn "curl nicht verfügbar, Health-Check übersprungen."
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
  - Frontend-Container konfigurieren (install_frontend_ct.sh).

SUMMARY

