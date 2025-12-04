#!/usr/bin/env bash
set -euo pipefail

log() { printf '[%(%Y-%m-%dT%H:%M:%S%z)T] [install-frontend] %s\n' -1 "$*"; }
warn() { printf '[%(%Y-%m-%dT%H:%M:%S%z)T] [install-frontend][WARN] %s\n' -1 "$*" >&2; }
abort() { printf '[%(%Y-%m-%dT%H:%M:%S%z)T] [install-frontend][ERROR] %s\n' -1 "$*" >&2; exit 1; }

trap 'abort "Fehler (exit $?) bei Befehl \"${BASH_COMMAND}\" in Zeile ${LINENO}."' ERR

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  abort "Bitte als root bzw. mit sudo ausführen."
fi

export LC_ALL=C.UTF-8 LANG=C.UTF-8
umask 022

REPO_URL="${REPO_URL:-https://github.com/TheRealByteCommander/Stundenzettel_web.git}"
REPO_BRANCH="${REPO_BRANCH:-main}"
INSTALL_DIR="${INSTALL_DIR:-/opt/tick-guard}"
PROJECT_DIR="${PROJECT_DIR:-$INSTALL_DIR/Stundenzettel_web}"
FRONTEND_DIR="$PROJECT_DIR/frontend"
WEB_ROOT="${WEB_ROOT:-/var/www/tick-guard}"
FRONTEND_IP="${FRONTEND_IP:-192.168.178.156}"
DDNS_DOMAIN="${DDNS_DOMAIN:-$FRONTEND_IP}"
PUBLIC_HOST="${PUBLIC_HOST:-$DDNS_DOMAIN}"
BACKEND_HOST="${BACKEND_HOST:-192.168.178.157}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
BACKEND_SCHEME="${BACKEND_SCHEME:-http}"
RUN_CERTBOT="${RUN_CERTBOT:-false}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-}"

log "Installationsparameter:"
log "  Repository:        $REPO_URL (Branch: $REPO_BRANCH)"
log "  Installationspfad: $PROJECT_DIR"
log "  Öffentlicher Host: $PUBLIC_HOST"
log "  Backend-Service:   $BACKEND_SCHEME://$BACKEND_HOST:$BACKEND_PORT"

if [[ "$DDNS_DOMAIN" == "$FRONTEND_IP" ]]; then
  log "Hinweis: Frontend wird IP-basiert ausgeliefert (Host: $PUBLIC_HOST)."
fi

export DEBIAN_FRONTEND=noninteractive
log "System aktualisieren und Basis-Konfiguration durchführen…"
apt-get update -y
apt-get upgrade -y

# Zeitzone auf Europe/Berlin setzen (falls nicht bereits gesetzt)
if [[ -f /etc/timezone ]] && [[ "$(cat /etc/timezone)" != "Europe/Berlin" ]]; then
  log "Zeitzone auf Europe/Berlin setzen…"
  timedatectl set-timezone Europe/Berlin || warn "Zeitzone konnte nicht gesetzt werden."
fi

log "Basis-Pakete installieren…"
apt-get install -y curl git rsync ufw nginx ca-certificates gnupg lsb-release

install_node() {
  log "Node.js >= 18 installieren (NodeSource 20.x)…"
  local setup_script="/tmp/nodesource_setup.sh"
  curl -fsSL https://deb.nodesource.com/setup_20.x -o "$setup_script"
  bash "$setup_script"
  rm -f "$setup_script"
  apt-get install -y nodejs
}

if command -v node >/dev/null 2>&1; then
  NODE_MAJOR="$(node -v | sed 's/^v//' | cut -d. -f1)"
  if (( NODE_MAJOR < 18 )); then
    install_node
  fi
else
  install_node
fi

if ! command -v npm >/dev/null 2>&1; then
  abort "npm konnte nicht gefunden werden. Prüfe bitte die Node.js-Installation."
fi

log "Repository vorbereiten…"
mkdir -p "$INSTALL_DIR"
if [[ -d "$PROJECT_DIR/.git" ]]; then
  # Sicherheitsprüfung für dieses Verzeichnis deaktivieren (wird als root ausgeführt)
  git config --global --add safe.directory "$PROJECT_DIR" || true
  git -C "$PROJECT_DIR" fetch --all --prune
  git -C "$PROJECT_DIR" reset --hard "origin/$REPO_BRANCH"
else
  git clone --depth 1 --branch "$REPO_BRANCH" "$REPO_URL" "$PROJECT_DIR"
  # Sicherheitsprüfung für das neu geklonte Verzeichnis deaktivieren
  git config --global --add safe.directory "$PROJECT_DIR" || true
fi

cd "$FRONTEND_DIR"

if [[ ! -f package.json ]]; then
  abort "Frontend-Verzeichnis $FRONTEND_DIR ist unvollständig (package.json fehlt)."
fi

log "Frontend-Abhängigkeiten installieren…"
npm install --legacy-peer-deps

ENV_FILE="$FRONTEND_DIR/.env.production"
if [[ -n "${PUBLIC_BACKEND_URL:-}" ]]; then
  log ".env.production schreiben ($ENV_FILE)…"
  printf 'VITE_API_BASE_URL=%s\n' "$PUBLIC_BACKEND_URL" > "$ENV_FILE"
else
  if [[ -f "$ENV_FILE" ]]; then
    log ".env.production entfernen – verwende relative /api-Routen."
    rm -f "$ENV_FILE"
  else
    log "Keine PUBLIC_BACKEND_URL gesetzt – verwende relative /api-Routen (erfordert Nginx-Proxy)."
  fi
fi

log "Frontend build ausführen…"
if ! npm run build; then
  abort "npm run build fehlgeschlagen."
fi

log "Build nach $WEB_ROOT deployen…"
mkdir -p "$WEB_ROOT"
rsync -a --delete "$FRONTEND_DIR/build/" "$WEB_ROOT/"
chown -R www-data:www-data "$WEB_ROOT"

log "Nginx-Konfiguration erstellen…"
cat >/etc/nginx/conf.d/tick-guard-rate-limit.conf <<'EOF'
limit_req_zone $binary_remote_addr zone=tick_guard_api:10m rate=10r/s;
EOF

COMMON_SNIPPET=/etc/nginx/snippets/tick-guard-common.conf
cat >"$COMMON_SNIPPET" <<EOF
root $WEB_ROOT;
index index.html;

location /api/ {
    proxy_pass $BACKEND_SCHEME://$BACKEND_HOST:$BACKEND_PORT/api/;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_buffering off;
    
    # Timeouts für längere Requests
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
    
    # Error Handling
    proxy_next_upstream error timeout invalid_header http_500 http_502 http_503;
    proxy_next_upstream_tries 2;
    proxy_next_upstream_timeout 10s;
    
    limit_req zone=tick_guard_api burst=20 nodelay;
}

location /health {
    proxy_pass $BACKEND_SCHEME://$BACKEND_HOST:$BACKEND_PORT/health;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-Proto \$scheme;
    access_log off;
}

location / {
    try_files \$uri /index.html;
    # Cache-Control für HTML - keine Caching
    add_header Cache-Control "no-cache, no-store, must-revalidate";
    add_header Pragma "no-cache";
    add_header Expires "0";
}

# JS/CSS-Dateien mit Cache-Control
location ~* \.(js|css|mjs)$ {
    add_header Cache-Control "public, max-age=0, must-revalidate";
    expires -1;
}

location /.well-known/acme-challenge/ {
    root /var/www/letsencrypt;
    default_type "text/plain";
}
EOF

mkdir -p /var/www/letsencrypt

NGINX_SITE=/etc/nginx/sites-available/tick-guard
cat >"$NGINX_SITE" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $PUBLIC_HOST;

    include snippets/tick-guard-common.conf;
}
EOF

CERT_PATH="/etc/letsencrypt/live/$PUBLIC_HOST/fullchain.pem"
KEY_PATH="/etc/letsencrypt/live/$PUBLIC_HOST/privkey.pem"

if [[ -f "$CERT_PATH" && -f "$KEY_PATH" ]]; then
  log "Bestehendes TLS-Zertifikat gefunden – HTTPS-Serverblock aktivieren."
  cat >>"$NGINX_SITE" <<EOF

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $PUBLIC_HOST;

    ssl_certificate $CERT_PATH;
    ssl_certificate_key $KEY_PATH;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header Referrer-Policy no-referrer;

    include snippets/tick-guard-common.conf;
}
EOF
fi

ln -sf "$NGINX_SITE" /etc/nginx/sites-enabled/tick-guard

log "Nginx Konfiguration testen…"
nginx -t
systemctl enable --now nginx
systemctl reload nginx

if command -v ufw >/dev/null 2>&1; then
  ufw allow 80/tcp >/dev/null 2>&1 || warn "Konnte Port 80 in UFW nicht öffnen."
  ufw allow 443/tcp >/dev/null 2>&1 || warn "Konnte Port 443 in UFW nicht öffnen."
  if ufw status | grep -q "inactive"; then
    ufw --force enable >/dev/null 2>&1 || warn "UFW konnte nicht aktiviert werden."
  fi
fi

if [[ "${RUN_CERTBOT,,}" == "true" ]]; then
  if [[ "$PUBLIC_HOST" =~ ^[0-9.]+$ ]]; then
    warn "Certbot wurde angefordert, aber $PUBLIC_HOST sieht nach einer IP aus. Überspringe Zertifikatserstellung."
  else
    if [[ -z "$CERTBOT_EMAIL" ]]; then
      abort "RUN_CERTBOT=true gesetzt, aber CERTBOT_EMAIL fehlt."
    fi
    log "Certbot ausführen…"
    apt-get install -y certbot python3-certbot-nginx
    if certbot --nginx -d "$PUBLIC_HOST" -m "$CERTBOT_EMAIL" --agree-tos --non-interactive --redirect; then
      nginx -t && systemctl reload nginx
    else
      warn "Certbot konnte kein Zertifikat ausstellen."
    fi
  fi
fi

# Health-Check
log "Frontend-Health-Check wird durchgeführt..."
if command -v curl >/dev/null 2>&1; then
  MAX_RETRIES=3
  RETRY_COUNT=0
  while [[ $RETRY_COUNT -lt $MAX_RETRIES ]]; do
    if curl -sSf "http://$PUBLIC_HOST/" >/dev/null; then
      log "✅ Frontend erreichbar unter http://$PUBLIC_HOST/"
      break
    else
      RETRY_COUNT=$((RETRY_COUNT + 1))
      if [[ $RETRY_COUNT -lt $MAX_RETRIES ]]; then
        log "Frontend-Check fehlgeschlagen - warte 2 Sekunden und versuche es erneut ($RETRY_COUNT/$MAX_RETRIES)..."
        sleep 2
      else
        warn "⚠️  Frontend-Check fehlgeschlagen nach $MAX_RETRIES Versuchen"
      fi
    fi
  done
else
  warn "curl nicht verfügbar - Frontend-Check übersprungen"
fi

log "Installation abgeschlossen. Teste Frontend unter http://$PUBLIC_HOST/"

cat <<SUMMARY

✅ Automatische Installation abgeschlossen.

Wichtige Pfade:
  Projektpfad:  $PROJECT_DIR
  Frontend:     $FRONTEND_DIR
  Build-Ziel:   $WEB_ROOT
  Nginx-Site:   $NGINX_SITE
  Common Rules: $COMMON_SNIPPET

Falls TLS benötigt wird:
  sudo RUN_CERTBOT=true CERTBOT_EMAIL=admin@$PUBLIC_HOST PUBLIC_HOST=$PUBLIC_HOST DDNS_DOMAIN=$PUBLIC_HOST bash scripts/install_frontend_ct.sh

Update-Script:
  - Für zukünftige Updates: sudo scripts/update_frontend.sh

SUMMARY

