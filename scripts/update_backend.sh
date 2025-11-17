#!/usr/bin/env bash
set -euo pipefail

log() { printf '[%(%Y-%m-%dT%H:%M:%S%z)T] [update-backend] %s\n' -1 "$*"; }
warn() { printf '[%(%Y-%m-%dT%H:%M:%S%z)T] [update-backend][WARN] %s\n' -1 "$*" >&2; }
abort() { printf '[%(%Y-%m-%dT%H:%M:%S%z)T] [update-backend][ERROR] %s\n' -1 "$*" >&2; exit 1; }

trap 'abort "Fehler (exit $?) bei Befehl \"${BASH_COMMAND}\" in Zeile ${LINENO}."' ERR

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  abort "Bitte als root bzw. mit sudo ausführen."
fi

umask 022

# Konfiguration
INSTALL_DIR="${INSTALL_DIR:-/opt/tick-guard}"
PROJECT_DIR="${PROJECT_DIR:-$INSTALL_DIR/Stundenzettel_web}"
BACKEND_DIR="$PROJECT_DIR/backend"
SERVICE_NAME="${SERVICE_NAME:-tick-guard-backend}"
SERVICE_USER="${SERVICE_USER:-tickguard}"
REPO_BRANCH="${REPO_BRANCH:-main}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/tick-guard}"
SKIP_BACKUP="${SKIP_BACKUP:-false}"

log "Backend-Update wird durchgeführt..."
log "  Projektpfad: $PROJECT_DIR"
log "  Backend-Verzeichnis: $BACKEND_DIR"
log "  Service: $SERVICE_NAME"
log "  Branch: $REPO_BRANCH"

# Prüfe ob Backend-Verzeichnis existiert
if [[ ! -d "$BACKEND_DIR" ]]; then
  abort "Backend-Verzeichnis $BACKEND_DIR existiert nicht. Bitte zuerst installieren."
fi

# Prüfe ob Service existiert
if ! systemctl list-unit-files | grep -q "^${SERVICE_NAME}\.service"; then
  abort "Service $SERVICE_NAME existiert nicht. Bitte zuerst installieren."
fi

# Backup erstellen (optional)
if [[ "${SKIP_BACKUP}" != "true" ]]; then
  log "Backup wird erstellt..."
  BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
  BACKUP_PATH="${BACKUP_DIR}/backend_${BACKUP_TIMESTAMP}"
  mkdir -p "$BACKUP_DIR"
  
  # Backup von .env und wichtigen Dateien
  if [[ -f "$BACKEND_DIR/.env" ]]; then
    mkdir -p "$BACKUP_PATH"
    cp -a "$BACKEND_DIR/.env" "$BACKUP_PATH/.env.backup"
    log "Backup erstellt: $BACKUP_PATH/.env.backup"
  fi
  
  # Alte Backups aufräumen (behalte nur die letzten 5)
  find "$BACKUP_DIR" -maxdepth 1 -type d -name "backend_*" | sort -r | tail -n +6 | xargs rm -rf 2>/dev/null || true
fi

# Service stoppen
log "Service $SERVICE_NAME wird gestoppt..."
systemctl stop "$SERVICE_NAME" || warn "Service konnte nicht gestoppt werden (möglicherweise bereits gestoppt)"

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
git fetch origin "$REPO_BRANCH"
git checkout "$REPO_BRANCH"
git pull origin "$REPO_BRANCH"

# Prüfe ob requirements.txt geändert wurde
cd "$BACKEND_DIR"
REQUIREMENTS_CHANGED=false
if [[ -f "requirements.txt" ]]; then
  if git diff HEAD@{1} HEAD -- requirements.txt | grep -q "^+"; then
    REQUIREMENTS_CHANGED=true
    log "requirements.txt wurde geändert - Abhängigkeiten werden aktualisiert..."
  fi
fi

# Python-Abhängigkeiten aktualisieren
if [[ "$REQUIREMENTS_CHANGED" == "true" ]] || [[ "${FORCE_UPDATE_DEPS:-false}" == "true" ]]; then
  log "Python-Abhängigkeiten werden aktualisiert..."
  if [[ ! -d "venv" ]]; then
    warn "Virtualenv nicht gefunden - wird neu erstellt..."
    python3 -m venv venv
  fi
  
  # shellcheck disable=SC1091
  source venv/bin/activate
  pip install --upgrade pip wheel
  pip install -r requirements.txt --upgrade
  deactivate
else
  log "requirements.txt unverändert - Abhängigkeiten werden übersprungen (setze FORCE_UPDATE_DEPS=true zum Erzwingen)"
fi

# .env Datei prüfen und aktualisieren (nur neue Variablen hinzufügen, bestehende nicht überschreiben)
if [[ -f ".env" ]]; then
  log ".env Datei wird geprüft..."
  
  # Prüfe und korrigiere LOCAL_RECEIPTS_PATH (muss absolut sein)
  if grep -q "^LOCAL_RECEIPTS_PATH=" .env; then
    CURRENT_PATH=$(grep "^LOCAL_RECEIPTS_PATH=" .env | cut -d= -f2- | xargs)
    if [[ -n "$CURRENT_PATH" ]] && [[ ! "$CURRENT_PATH" = /* ]]; then
      warn "LOCAL_RECEIPTS_PATH ist nicht absolut: '$CURRENT_PATH' - wird korrigiert..."
      # Korrigiere zu absolutem Pfad
      ABSOLUTE_PATH="/var/tick-guard/receipts"
      sed -i "s|^LOCAL_RECEIPTS_PATH=.*|LOCAL_RECEIPTS_PATH=$ABSOLUTE_PATH|" .env
      log "LOCAL_RECEIPTS_PATH korrigiert zu: $ABSOLUTE_PATH"
      # Stelle sicher, dass das Verzeichnis existiert
      mkdir -p "$ABSOLUTE_PATH"
      chown -R "$SERVICE_USER":"$SERVICE_USER" "$ABSOLUTE_PATH" 2>/dev/null || true
    fi
  fi
  
  # Prüfe ob neue Variablen in .env.example existieren (falls vorhanden)
  if [[ -f ".env.example" ]]; then
    while IFS= read -r line; do
      # Überspringe Kommentare und leere Zeilen
      [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
      # Extrahiere Variablenname
      VAR_NAME=$(echo "$line" | cut -d= -f1 | xargs)
      # Prüfe ob Variable bereits in .env existiert
      if ! grep -q "^${VAR_NAME}=" .env; then
        warn "Neue Variable $VAR_NAME gefunden in .env.example - bitte manuell prüfen und hinzufügen"
      fi
    done < .env.example
  fi
else
  warn ".env Datei nicht gefunden - bitte manuell erstellen"
fi

# Service neu starten
log "Service $SERVICE_NAME wird neu gestartet..."
systemctl daemon-reload
systemctl start "$SERVICE_NAME"

# Warte kurz auf Service-Start
sleep 3

# Status prüfen
log "Service-Status wird geprüft..."
if systemctl is-active --quiet "$SERVICE_NAME"; then
  log "✅ Service $SERVICE_NAME läuft erfolgreich"
else
  warn "❌ Service $SERVICE_NAME konnte nicht gestartet werden"
  log "Letzte Service-Logs (Fehleranalyse):"
  journalctl -u "$SERVICE_NAME" -n 30 --no-pager || true
  log "Versuche Service-Status anzuzeigen:"
  systemctl status "$SERVICE_NAME" --no-pager -l || true
  abort "Service konnte nicht gestartet werden. Bitte Logs prüfen: journalctl -u $SERVICE_NAME -n 50"
fi

# Health-Check
log "Health-Check wird durchgeführt..."
if command -v curl >/dev/null 2>&1; then
  MAX_RETRIES=5
  RETRY_COUNT=0
  while [[ $RETRY_COUNT -lt $MAX_RETRIES ]]; do
    if curl -sSf http://localhost:8000/health >/dev/null 2>&1; then
      log "✅ Health-Check erfolgreich"
      break
    else
      RETRY_COUNT=$((RETRY_COUNT + 1))
      if [[ $RETRY_COUNT -lt $MAX_RETRIES ]]; then
        log "Health-Check fehlgeschlagen - warte 2 Sekunden und versuche es erneut ($RETRY_COUNT/$MAX_RETRIES)..."
        sleep 2
      else
        warn "⚠️  Health-Check fehlgeschlagen nach $MAX_RETRIES Versuchen - bitte Logs prüfen"
      fi
    fi
  done
else
  warn "curl nicht verfügbar - Health-Check übersprungen"
fi

# Logs anzeigen (letzte 20 Zeilen)
log "Letzte Service-Logs:"
journalctl -u "$SERVICE_NAME" -n 20 --no-pager || warn "Logs konnten nicht angezeigt werden"

cat <<SUMMARY

✅ Backend-Update erfolgreich abgeschlossen!

Wichtige Informationen:
  Projektpfad:   $PROJECT_DIR
  Backend:       $BACKEND_DIR
  Service:       $SERVICE_NAME
  Status:        $(systemctl is-active "$SERVICE_NAME")
  
Nächste Schritte:
  - Prüfe die Logs: journalctl -u $SERVICE_NAME -f
  - Teste die API: curl http://localhost:8000/health
  - Prüfe .env auf neue Variablen (falls .env.example vorhanden)

Bei Problemen:
  - Logs ansehen: journalctl -u $SERVICE_NAME -n 50
  - Service neu starten: systemctl restart $SERVICE_NAME
  - Backup wiederherstellen: cp $BACKUP_PATH/.env.backup $BACKEND_DIR/.env

SUMMARY

