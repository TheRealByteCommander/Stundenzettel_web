#!/usr/bin/env bash
set -euo pipefail

log() { printf '[%(%Y-%m-%dT%H:%M:%S%z)T] [update-frontend] %s\n' -1 "$*"; }
warn() { printf '[%(%Y-%m-%dT%H:%M:%S%z)T] [update-frontend][WARN] %s\n' -1 "$*" >&2; }
abort() { printf '[%(%Y-%m-%dT%H:%M:%S%z)T] [update-frontend][ERROR] %s\n' -1 "$*" >&2; exit 1; }

trap 'abort "Fehler (exit $?) bei Befehl \"${BASH_COMMAND}\" in Zeile ${LINENO}."' ERR

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  abort "Bitte als root bzw. mit sudo ausführen."
fi

export LC_ALL=C.UTF-8 LANG=C.UTF-8
umask 022

# Konfiguration
INSTALL_DIR="${INSTALL_DIR:-/opt/tick-guard}"
PROJECT_DIR="${PROJECT_DIR:-$INSTALL_DIR/Stundenzettel_web}"
FRONTEND_DIR="$PROJECT_DIR/frontend"
WEB_ROOT="${WEB_ROOT:-/var/www/tick-guard}"
REPO_BRANCH="${REPO_BRANCH:-main}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/tick-guard}"
SKIP_BACKUP="${SKIP_BACKUP:-false}"
SKIP_BUILD="${SKIP_BUILD:-false}"

log "Frontend-Update wird durchgeführt..."
log "  Projektpfad: $PROJECT_DIR"
log "  Frontend-Verzeichnis: $FRONTEND_DIR"
log "  Web-Root: $WEB_ROOT"
log "  Branch: $REPO_BRANCH"

# Prüfe ob Frontend-Verzeichnis existiert
if [[ ! -d "$FRONTEND_DIR" ]]; then
  abort "Frontend-Verzeichnis $FRONTEND_DIR existiert nicht. Bitte zuerst installieren."
fi

# Prüfe ob package.json existiert
if [[ ! -f "$FRONTEND_DIR/package.json" ]]; then
  abort "package.json nicht gefunden in $FRONTEND_DIR"
fi

# Backup erstellen (optional)
if [[ "${SKIP_BACKUP}" != "true" ]]; then
  log "Backup wird erstellt..."
  BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
  BACKUP_PATH="${BACKUP_DIR}/frontend_${BACKUP_TIMESTAMP}"
  mkdir -p "$BACKUP_DIR"
  
  # Backup von .env.production und build-Ordner
  if [[ -f "$FRONTEND_DIR/.env.production" ]]; then
    mkdir -p "$BACKUP_PATH"
    cp -a "$FRONTEND_DIR/.env.production" "$BACKUP_PATH/.env.production.backup"
    log "Backup erstellt: $BACKUP_PATH/.env.production.backup"
  fi
  
  # Backup des aktuellen Builds
  if [[ -d "$WEB_ROOT" ]]; then
    mkdir -p "$BACKUP_PATH"
    cp -a "$WEB_ROOT" "$BACKUP_PATH/build.backup" 2>/dev/null || warn "Build-Backup konnte nicht erstellt werden"
  fi
  
  # Alte Backups aufräumen (behalte nur die letzten 5)
  find "$BACKUP_DIR" -maxdepth 1 -type d -name "frontend_*" | sort -r | tail -n +6 | xargs rm -rf 2>/dev/null || true
fi

# Git-Update
log "Repository wird aktualisiert..."
cd "$PROJECT_DIR"

# Prüfe ob .git existiert
if [[ ! -d ".git" ]]; then
  abort "Kein Git-Repository gefunden in $PROJECT_DIR"
fi

# Aktuellen Branch speichern
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
log "Aktueller Branch: $CURRENT_BRANCH"

# Änderungen stashen (falls vorhanden)
if ! git diff-index --quiet HEAD --; then
  warn "Uncommitted Änderungen gefunden. Diese werden gestasht."
  git stash push -m "Auto-stash vor Update $(date +%Y%m%d_%H%M%S)"
fi

# Fetch und Pull
log "Änderungen werden geholt..."
# Sicherheitsprüfung für dieses Verzeichnis deaktivieren (wird als root ausgeführt)
git config --global --add safe.directory "$PROJECT_DIR" || true
git fetch origin "$REPO_BRANCH"
git checkout "$REPO_BRANCH"
git pull origin "$REPO_BRANCH"

cd "$FRONTEND_DIR"

# Prüfe ob package.json oder package-lock.json geändert wurde
PACKAGE_CHANGED=false
if [[ -f "package.json" ]]; then
  if git diff HEAD@{1} HEAD -- package.json package-lock.json 2>/dev/null | grep -q "^+"; then
    PACKAGE_CHANGED=true
    log "package.json oder package-lock.json wurde geändert - Abhängigkeiten werden aktualisiert..."
  fi
fi

# Node-Abhängigkeiten aktualisieren
if [[ "$PACKAGE_CHANGED" == "true" ]] || [[ "${FORCE_UPDATE_DEPS:-false}" == "true" ]]; then
  log "Node-Abhängigkeiten werden aktualisiert..."
  
  # Prüfe Node.js Version
  if ! command -v node >/dev/null 2>&1; then
    abort "Node.js ist nicht installiert"
  fi
  
  NODE_MAJOR=$(node -v | sed 's/^v//' | cut -d. -f1)
  if (( NODE_MAJOR < 18 )); then
    abort "Node.js Version 18+ erforderlich (aktuell: $(node -v))"
  fi
  
  # npm install
  log "npm install wird ausgeführt..."
  npm install --legacy-peer-deps
else
  log "package.json unverändert - Abhängigkeiten werden übersprungen (setze FORCE_UPDATE_DEPS=true zum Erzwingen)"
fi

# .env.production prüfen
if [[ -f ".env.production" ]]; then
  log ".env.production gefunden - wird beibehalten"
else
  log ".env.production nicht gefunden - wird erstellt (falls PUBLIC_BACKEND_URL gesetzt)"
  if [[ -n "${PUBLIC_BACKEND_URL:-}" ]]; then
    printf 'VITE_API_BASE_URL=%s\n' "$PUBLIC_BACKEND_URL" > .env.production
    log ".env.production erstellt mit VITE_API_BASE_URL=$PUBLIC_BACKEND_URL"
  else
    log "Hinweis: Keine PUBLIC_BACKEND_URL gesetzt - Frontend verwendet relative /api-Routen (erfordert Nginx-Proxy)"
  fi
fi

# Frontend builden
if [[ "${SKIP_BUILD}" != "true" ]]; then
  log "Frontend wird gebaut..."
  if ! npm run build; then
    abort "npm run build fehlgeschlagen"
  fi
  log "✅ Build erfolgreich"
else
  log "Build wird übersprungen (SKIP_BUILD=true gesetzt)"
fi

# Build deployen
if [[ -d "build" ]]; then
  log "Build wird nach $WEB_ROOT deployt..."
  mkdir -p "$WEB_ROOT"
  
  # Alten Build sichern (für Rollback)
  if [[ -d "$WEB_ROOT" ]] && [[ "$(ls -A $WEB_ROOT 2>/dev/null)" ]]; then
    mv "$WEB_ROOT" "${WEB_ROOT}.old.$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
  fi
  
  # Neuen Build kopieren
  rsync -a --delete "$FRONTEND_DIR/build/" "$WEB_ROOT/"
  chown -R www-data:www-data "$WEB_ROOT"
  log "✅ Build erfolgreich deployt"
else
  abort "Build-Verzeichnis nicht gefunden"
fi

# Nginx-Konfiguration testen
log "Nginx-Konfiguration wird getestet..."
if nginx -t 2>/dev/null; then
  log "✅ Nginx-Konfiguration ist gültig"
  systemctl reload nginx || warn "Nginx konnte nicht neu geladen werden"
else
  warn "⚠️  Nginx-Konfigurationstest fehlgeschlagen - bitte manuell prüfen"
fi

# Health-Check
log "Frontend-Health-Check wird durchgeführt..."
if command -v curl >/dev/null 2>&1; then
  MAX_RETRIES=3
  RETRY_COUNT=0
  while [[ $RETRY_COUNT -lt $MAX_RETRIES ]]; do
    if curl -sSf http://localhost/ >/dev/null 2>&1; then
      log "✅ Frontend erreichbar"
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

# Alte Builds aufräumen (behalte nur die letzten 3)
log "Alte Build-Backups werden aufgeräumt..."
find "$(dirname "$WEB_ROOT")" -maxdepth 1 -type d -name "$(basename "$WEB_ROOT").old.*" | sort -r | tail -n +4 | xargs rm -rf 2>/dev/null || true

cat <<SUMMARY

✅ Frontend-Update erfolgreich abgeschlossen!

Wichtige Informationen:
  Projektpfad:   $PROJECT_DIR
  Frontend:      $FRONTEND_DIR
  Web-Root:      $WEB_ROOT
  Build-Status:  ✅ Erfolgreich
  
Nächste Schritte:
  - Teste das Frontend: http://$(hostname -I | awk '{print $1}')/
  - Prüfe Nginx-Logs: tail -f /var/log/nginx/error.log
  - Prüfe .env.production auf neue Variablen

Bei Problemen:
  - Nginx-Logs: tail -f /var/log/nginx/error.log /var/log/nginx/access.log
  - Nginx neu laden: systemctl reload nginx
  - Build-Backup wiederherstellen: rsync -a ${WEB_ROOT}.old.*/ $WEB_ROOT/

SUMMARY

