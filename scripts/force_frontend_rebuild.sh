#!/usr/bin/env bash
set -euo pipefail

log() { printf '[%(%Y-%m-%dT%H:%M:%S%z)T] [force-rebuild] %s\n' -1 "$*"; }
warn() { printf '[%(%Y-%m-%dT%H:%M:%S%z)T] [force-rebuild][WARN] %s\n' -1 "$*" >&2; }
abort() { printf '[%(%Y-%m-%dT%H:%M:%S%z)T] [force-rebuild][ERROR] %s\n' -1 "$*" >&2; exit 1; }

PROJECT_DIR="${PROJECT_DIR:-/opt/tick-guard/Stundenzettel_web}"
FRONTEND_DIR="${FRONTEND_DIR:-$PROJECT_DIR/frontend}"
WEB_ROOT="${WEB_ROOT:-/var/www/tick-guard}"

if [[ ! -d "$FRONTEND_DIR" ]]; then
  abort "Frontend-Verzeichnis nicht gefunden: $FRONTEND_DIR"
fi

cd "$FRONTEND_DIR"

log "Frontend-Force-Rebuild wird durchgeführt..."
log "  Projektpfad: $PROJECT_DIR"
log "  Frontend: $FRONTEND_DIR"
log "  Web-Root: $WEB_ROOT"

# Alte Builds löschen
log "Alte Build-Verzeichnisse werden gelöscht..."
rm -rf "$FRONTEND_DIR/build" "$FRONTEND_DIR/dist" "$FRONTEND_DIR/.vite" 2>/dev/null || true

# node_modules prüfen und ggf. neu installieren
log "Abhängigkeiten werden geprüft..."
if [[ ! -d "$FRONTEND_DIR/node_modules" ]] || [[ -n "${FORCE_UPDATE_DEPS:-}" ]]; then
  log "Abhängigkeiten werden installiert..."
  npm install --legacy-peer-deps
else
  log "Abhängigkeiten vorhanden - überspringe Installation"
fi

# TypeScript-Cache löschen
log "TypeScript-Cache wird gelöscht..."
rm -rf "$FRONTEND_DIR/tsconfig.tsbuildinfo" 2>/dev/null || true

# .env.production entfernen (verwendet relative /api-Routen)
if [[ -f "$FRONTEND_DIR/.env.production" ]]; then
  log ".env.production wird entfernt (verwendet relative /api-Routen)..."
  rm -f "$FRONTEND_DIR/.env.production"
fi

# Build mit Clean
log "Frontend wird neu gebaut (clean build)..."
if ! npm run build; then
  abort "npm run build fehlgeschlagen"
fi

# Prüfe ob Build-Verzeichnis existiert
BUILD_DIR="$FRONTEND_DIR/build"
if [[ ! -d "$BUILD_DIR" ]]; then
  BUILD_DIR="$FRONTEND_DIR/dist"
fi

if [[ -d "$BUILD_DIR" ]]; then
  log "Build-Verzeichnis gefunden: $BUILD_DIR"
  
  # Backup erstellen
  if [[ -d "$WEB_ROOT" ]]; then
    BACKUP_DIR="${WEB_ROOT}.old.$(date +%Y%m%d_%H%M%S)"
    log "Backup wird erstellt: $BACKUP_DIR"
    cp -a "$WEB_ROOT" "$BACKUP_DIR" 2>/dev/null || warn "Backup konnte nicht erstellt werden"
  fi
  
  # Deploy
  log "Build wird nach $WEB_ROOT deployt..."
  mkdir -p "$WEB_ROOT"
  rsync -a --delete "$BUILD_DIR/" "$WEB_ROOT/"
  chown -R www-data:www-data "$WEB_ROOT"
  
  log "✅ Build erfolgreich deployt"
  
  # Prüfe Build-Datum
  if [[ -f "$WEB_ROOT/index.html" ]]; then
    BUILD_TIME=$(stat -c %y "$WEB_ROOT/index.html" 2>/dev/null || stat -f "%Sm" "$WEB_ROOT/index.html" 2>/dev/null || echo "unbekannt")
    log "Build-Zeitpunkt: $BUILD_TIME"
  fi
  
  # Prüfe ob neue Dateien vorhanden sind
  if [[ -f "$WEB_ROOT/assets/index-"*.js ]]; then
    JS_FILE=$(ls -t "$WEB_ROOT/assets/index-"*.js 2>/dev/null | head -1)
    if [[ -n "$JS_FILE" ]]; then
      JS_SIZE=$(stat -c %s "$JS_FILE" 2>/dev/null || stat -f "%z" "$JS_FILE" 2>/dev/null || echo "0")
      log "Haupt-JS-Datei: $(basename "$JS_FILE") (Größe: $JS_SIZE bytes)"
    fi
  fi
else
  abort "Build-Verzeichnis nicht gefunden (weder build noch dist)"
fi

# Nginx neu laden
log "Nginx wird neu geladen..."
if nginx -t 2>/dev/null; then
  systemctl reload nginx || warn "Nginx konnte nicht neu geladen werden"
  log "✅ Nginx neu geladen"
else
  warn "⚠️  Nginx-Konfigurationstest fehlgeschlagen"
fi

cat <<SUMMARY

✅ Frontend-Force-Rebuild erfolgreich abgeschlossen!

Wichtige Informationen:
  Projektpfad:   $PROJECT_DIR
  Frontend:      $FRONTEND_DIR
  Web-Root:      $WEB_ROOT
  Build-Status:  ✅ Erfolgreich
  
Nächste Schritte:
  1. Browser-Cache leeren (Strg+Shift+R oder Strg+F5)
  2. Teste das Frontend: http://$(hostname -I | awk '{print $1}')/
  3. Prüfe Browser-Console auf Fehler (F12)
  4. Prüfe ob neue JS-Dateien geladen werden (Network-Tab)

Bei Problemen:
  - Browser-Cache komplett leeren
  - Incognito/Private-Modus testen
  - Prüfe Nginx-Logs: tail -f /var/log/nginx/error.log
  - Prüfe Build-Zeitpunkt oben

SUMMARY

