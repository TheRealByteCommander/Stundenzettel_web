#!/usr/bin/env bash
set -euo pipefail

log() { printf '[%(%Y-%m-%dT%H:%M:%S%z)T] [install-tools] %s\n' -1 "$*"; }
warn() { printf '[%(%Y-%m-%dT%H:%M:%S%z)T] [install-tools][WARN] %s\n' -1 "$*" >&2; }
abort() { printf '[%(%Y-%m-%dT%H:%M:%S%z)T] [install-tools][ERROR] %s\n' -1 "$*" >&2; exit 1; }

trap 'abort "Fehler (exit $?) bei Befehl \"${BASH_COMMAND}\" in Zeile ${LINENO}."' ERR

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  abort "Bitte als root bzw. mit sudo ausführen."
fi

# Standard-Pfade
BACKEND_DIR="${BACKEND_DIR:-/opt/tick-guard/Stundenzettel_web/backend}"
VENV_DIR="${VENV_DIR:-$BACKEND_DIR/venv}"

log "Installation aller Prioritäts-Tools"
log "Backend-Verzeichnis: $BACKEND_DIR"
log "Virtualenv-Verzeichnis: $VENV_DIR"

# Prüfe ob Backend-Verzeichnis existiert
if [[ ! -d "$BACKEND_DIR" ]]; then
  abort "Backend-Verzeichnis $BACKEND_DIR existiert nicht."
fi

# Prüfe ob Virtualenv existiert
if [[ ! -d "$VENV_DIR" ]]; then
  abort "Virtualenv $VENV_DIR existiert nicht. Bitte zuerst Backend installieren."
fi

cd "$BACKEND_DIR"

# Virtualenv aktivieren
log "Aktiviere Virtualenv…"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# Pip aktualisieren
log "Aktualisiere pip und wheel…"
pip install --upgrade pip wheel

# Priorität 1 Tools installieren
log "Installiere Priorität 1 Tools…"
log "  - imagehash (DuplicateDetectionTool)"
pip install imagehash>=4.3.1 || warn "imagehash konnte nicht installiert werden (optional)"

log "  - opencv-python (ImageQualityTool)"
pip install opencv-python>=4.8.0 || warn "opencv-python konnte nicht installiert werden (optional)"

log "  - pytz (TimeZoneTool)"
pip install pytz>=2023.3 || warn "pytz konnte nicht installiert werden (optional)"

log "  - timezonefinder (TimeZoneTool erweitert)"
pip install timezonefinder>=6.2.0 || warn "timezonefinder konnte nicht installiert werden (optional)"

log "  - dnspython (EmailValidatorTool)"
pip install dnspython>=2.4.0 || warn "dnspython konnte nicht installiert werden (optional)"

# Priorität 2 Tools installieren
log "Installiere Priorität 2 Tools…"
log "  - imapclient (EmailParserTool)"
pip install imapclient>=2.3.1 || warn "imapclient konnte nicht installiert werden (optional)"

log "  - openpyxl (ExcelImportExportTool)"
pip install openpyxl>=3.1.0 || warn "openpyxl konnte nicht installiert werden (optional)"

log "  - phonenumbers (PhoneNumberValidatorTool)"
pip install phonenumbers>=8.13.0 || warn "phonenumbers konnte nicht installiert werden (optional)"

log "  - holidays (bereits in requirements.txt, prüfe Installation)"
pip install holidays>=0.36 || warn "holidays konnte nicht installiert werden (optional)"

# Priorität 3 Tools installieren
log "Installiere Priorität 3 Tools…"

# System-Pakete für pyzbar
log "  - libzbar0 und zbar-tools (System-Paket für pyzbar)"
if ! command -v zbarimg >/dev/null 2>&1; then
  log "    Installiere zbar System-Pakete…"
  apt-get update -y
  apt-get install -y libzbar0 zbar-tools || warn "zbar konnte nicht installiert werden (optional)"
else
  log "    zbar ist bereits installiert."
fi

log "  - pyzbar (QRCodeReaderTool, BarcodeReaderTool)"
pip install pyzbar>=0.1.9 || warn "pyzbar konnte nicht installiert werden (optional)"

log "  - pillow (Bildverarbeitung)"
pip install pillow>=10.0.0 || warn "pillow konnte nicht installiert werden (optional)"

# Virtualenv deaktivieren
deactivate

# Verifikation
log "Verifiziere Installation…"
source "$VENV_DIR/bin/activate"

VERIFICATION_FAILED=0

check_package() {
  local package=$1
  local import_cmd=$2
  if python3 -c "$import_cmd" >/dev/null 2>&1; then
    log "  ✅ $package OK"
    return 0
  else
    warn "  ❌ $package FEHLT"
    VERIFICATION_FAILED=1
    return 1
  fi
}

log "Prüfe Priorität 1 Tools:"
check_package "imagehash" "import imagehash"
check_package "opencv-python" "import cv2"
check_package "pytz" "import pytz"
check_package "timezonefinder" "import timezonefinder"
check_package "dnspython" "import dns.resolver"

log "Prüfe Priorität 2 Tools:"
check_package "imapclient" "import imapclient"
check_package "openpyxl" "import openpyxl"
check_package "phonenumbers" "import phonenumbers"
check_package "holidays" "import holidays"

log "Prüfe Priorität 3 Tools:"
check_package "pyzbar" "from pyzbar import decode"
check_package "pillow" "from PIL import Image"

deactivate

# Backend-Service neu starten (falls vorhanden)
SERVICE_NAME="${SERVICE_NAME:-tick-guard-backend}"
if systemctl list-unit-files | grep -q "^${SERVICE_NAME}\.service"; then
  log "Starte Backend-Service neu…"
  systemctl restart "$SERVICE_NAME" || warn "Service konnte nicht neu gestartet werden."
  sleep 2
  if systemctl is-active --quiet "$SERVICE_NAME"; then
    log "✅ Backend-Service läuft."
  else
    warn "⚠️  Backend-Service läuft nicht. Bitte Logs prüfen: journalctl -u $SERVICE_NAME"
  fi
else
  log "Kein Backend-Service gefunden. Bitte manuell neu starten."
fi

# Zusammenfassung
cat <<SUMMARY

═══════════════════════════════════════════════════════════════
Installation abgeschlossen
═══════════════════════════════════════════════════════════════

Installierte Tools:
  Priorität 1: imagehash, opencv-python, pytz, timezonefinder, dnspython
  Priorität 2: imapclient, openpyxl, phonenumbers, holidays
  Priorität 3: pyzbar, pillow (+ libzbar0 System-Paket)

Verifikation:
SUMMARY

if [[ $VERIFICATION_FAILED -eq 0 ]]; then
  log "✅ Alle Tools wurden erfolgreich installiert und verifiziert."
else
  warn "⚠️  Einige Tools konnten nicht verifiziert werden. Bitte manuell prüfen."
fi

cat <<SUMMARY

Nächste Schritte:
  1. Optional: API-Keys in $BACKEND_DIR/.env setzen:
     - WEATHER_API_KEY (für WeatherAPITool)
     - GOOGLE_MAPS_API_KEY oder OPENROUTESERVICE_API_KEY (für TravelTimeCalculatorTool)
  
  2. Backend-Service Status prüfen:
     systemctl status $SERVICE_NAME
  
  3. Logs prüfen:
     journalctl -u $SERVICE_NAME -f

═══════════════════════════════════════════════════════════════
SUMMARY

