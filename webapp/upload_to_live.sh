#!/bin/bash

# Schmitz Intralogistik - FTP Upload Script
# Lädt die komplette Anwendung auf den Live-Server hoch

echo "========================================"
echo "Schmitz Intralogistik - FTP Upload"
echo "========================================"

# FTP Konfiguration
FTP_HOST="ai.byte-commander.de"
FTP_USER="f017983a"
FTP_PASS="mAh4Raeder!"
FTP_DIR="/"

# Lokaler Pfad zur Webapp
LOCAL_PATH="/app/webapp"

echo "🚀 Uploading Schmitz Intralogistik Zeiterfassung..."
echo "Server: $FTP_HOST"
echo "User: $FTP_USER"

# FTP Upload mit lftp (falls verfügbar)
if command -v lftp >/dev/null 2>&1; then
    echo "Using lftp for upload..."
    lftp -f "
    open $FTP_HOST
    user $FTP_USER $FTP_PASS
    lcd $LOCAL_PATH
    cd $FTP_DIR
    mirror --reverse --delete --verbose
    bye
    "
else
    echo "⚠️  lftp not available. Manual FTP upload required."
    echo ""
    echo "FTP Upload Instructions:"
    echo "========================="
    echo "1. Connect to: $FTP_HOST"
    echo "2. Username: $FTP_USER"
    echo "3. Password: $FTP_PASS"
    echo "4. Upload all files from: $LOCAL_PATH"
    echo ""
    echo "Required files to upload:"
    echo "- index.html"
    echo "- assets/ (folder with css and js)"
    echo "- api/ (complete API folder)"
    echo "- .htaccess"
    echo "- *.md (documentation files)"
    echo ""
    echo "After upload:"
    echo "1. Visit: https://ai.byte-commander.de/api/install.php"
    echo "2. Database will be initialized automatically"
    echo "3. Login: admin@schmitz-intralogistik.de / admin123"
    echo "4. Delete install.php for security"
fi

echo ""
echo "✅ Upload preparation complete!"
echo ""
echo "Live URL after upload:"
echo "👉 https://ai.byte-commander.de"
echo ""
echo "Admin Login:"
echo "📧 admin@schmitz-intralogistik.de"
echo "🔒 admin123"
echo ""
echo "Database: d04464c7 (already configured)"
echo "IMPORTANT: Delete install.php after first setup!"