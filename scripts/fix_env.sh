#!/usr/bin/env bash
set -euo pipefail

# Script zum Korrigieren/Vervollständigen der .env Datei

BACKEND_DIR="${1:-/opt/tick-guard/Stundenzettel_web/backend}"
ENV_FILE="$BACKEND_DIR/.env"
SERVICE_USER="${SERVICE_USER:-tickguard}"

echo "🔧 Korrigiere .env Datei: $ENV_FILE"

# Prüfe ob .env existiert
if [[ ! -f "$ENV_FILE" ]]; then
  echo "❌ .env Datei nicht gefunden: $ENV_FILE"
  exit 1
fi

# Backup erstellen
cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo "✅ Backup erstellt"

# Stelle sicher, dass LOCAL_RECEIPTS_PATH gesetzt ist (absolut)
if ! grep -q "^LOCAL_RECEIPTS_PATH=" "$ENV_FILE"; then
  echo "➕ Füge LOCAL_RECEIPTS_PATH hinzu..."
  echo "LOCAL_RECEIPTS_PATH=/var/tick-guard/receipts" >> "$ENV_FILE"
else
  # Prüfe ob absolut
  CURRENT_PATH=$(grep "^LOCAL_RECEIPTS_PATH=" "$ENV_FILE" | cut -d= -f2- | tr -d '"' | xargs)
  if [[ -n "$CURRENT_PATH" ]] && [[ ! "$CURRENT_PATH" = /* ]]; then
    echo "🔧 Korrigiere LOCAL_RECEIPTS_PATH zu absolutem Pfad..."
    sed -i "s|^LOCAL_RECEIPTS_PATH=.*|LOCAL_RECEIPTS_PATH=/var/tick-guard/receipts|" "$ENV_FILE"
  fi
fi

# Stelle sicher, dass das Verzeichnis existiert
RECEIPTS_PATH=$(grep "^LOCAL_RECEIPTS_PATH=" "$ENV_FILE" | cut -d= -f2- | tr -d '"' | xargs)
if [[ -n "$RECEIPTS_PATH" ]]; then
  mkdir -p "$RECEIPTS_PATH"
  chown -R "$SERVICE_USER":"$SERVICE_USER" "$RECEIPTS_PATH" 2>/dev/null || true
  echo "✅ Verzeichnis erstellt: $RECEIPTS_PATH"
fi

# Prüfe andere wichtige Variablen
REQUIRED_VARS=(
  "SECRET_KEY"
  "ENCRYPTION_KEY"
)

for VAR in "${REQUIRED_VARS[@]}"; do
  if ! grep -q "^${VAR}=" "$ENV_FILE"; then
    echo "⚠️  Warnung: $VAR fehlt in .env"
    if [[ "$VAR" == "SECRET_KEY" ]]; then
      NEW_KEY=$(openssl rand -hex 32)
      echo "$VAR=$NEW_KEY" >> "$ENV_FILE"
      echo "➕ $VAR wurde generiert und hinzugefügt"
    elif [[ "$VAR" == "ENCRYPTION_KEY" ]]; then
      NEW_KEY=$(openssl rand -hex 32)
      echo "$VAR=$NEW_KEY" >> "$ENV_FILE"
      echo "➕ $VAR wurde generiert und hinzugefügt"
    fi
  fi
done

# Prüfe Ollama-Konfiguration
if ! grep -q "^OLLAMA_BASE_URL=" "$ENV_FILE"; then
  echo "➕ Füge OLLAMA_BASE_URL hinzu..."
  echo "OLLAMA_BASE_URL=http://192.168.178.155:11434" >> "$ENV_FILE"
fi

if ! grep -q "^OLLAMA_MODEL_CHAT=" "$ENV_FILE"; then
  echo "➕ Füge OLLAMA_MODEL_CHAT hinzu..."
  echo "OLLAMA_MODEL_CHAT=Qwen2.5:32B" >> "$ENV_FILE"
fi

if ! grep -q "^OLLAMA_MODEL_DOCUMENT=" "$ENV_FILE"; then
  echo "➕ Füge OLLAMA_MODEL_DOCUMENT hinzu..."
  echo "OLLAMA_MODEL_DOCUMENT=Qwen2.5vl:7b" >> "$ENV_FILE"
fi

if ! grep -q "^OLLAMA_MODEL_ACCOUNTING=" "$ENV_FILE"; then
  echo "➕ Füge OLLAMA_MODEL_ACCOUNTING hinzu..."
  echo "OLLAMA_MODEL_ACCOUNTING=DeepSeek-R1:32B" >> "$ENV_FILE"
fi

if ! grep -q "^OLLAMA_TIMEOUT=" "$ENV_FILE"; then
  echo "➕ Füge OLLAMA_TIMEOUT hinzu..."
  echo "OLLAMA_TIMEOUT=600" >> "$ENV_FILE"
fi

echo ""
echo "✅ .env Datei wurde korrigiert!"
echo ""
echo "Aktuelle .env Datei:"
echo "---"
cat "$ENV_FILE"
echo "---"
echo ""
echo "Nächste Schritte:"
echo "  systemctl restart tick-guard-backend"
echo "  systemctl status tick-guard-backend"

