#!/bin/bash

# Schmitz Intralogistik Zeiterfassung - Setup Script
# Dieses Script automatisiert die grundlegende Installation

echo "========================================"
echo "Schmitz Intralogistik - Zeiterfassung"
echo "Automatisches Setup-Script"
echo "========================================"

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funktionen
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

# System-Checks
echo "Schritt 1: System-Checks"
echo "----------------------------------------"

# PHP Version prüfen
if command -v php >/dev/null 2>&1; then
    PHP_VERSION=$(php -r "echo PHP_VERSION;")
    if php -r "exit(version_compare(PHP_VERSION, '7.4', '<') ? 1 : 0);"; then
        print_error "PHP 7.4+ erforderlich. Aktuelle Version: $PHP_VERSION"
        exit 1
    else
        print_success "PHP Version: $PHP_VERSION"
    fi
else
    print_error "PHP nicht installiert"
    exit 1
fi

# MySQL prüfen
if command -v mysql >/dev/null 2>&1; then
    print_success "MySQL verfügbar"
else
    print_warning "MySQL-Client nicht gefunden. Stelle sicher, dass MySQL-Server läuft."
fi

# Composer prüfen
if command -v composer >/dev/null 2>&1; then
    print_success "Composer verfügbar"
else
    print_error "Composer nicht installiert. Bitte installieren: https://getcomposer.org/"
    exit 1
fi

# PHP-Erweiterungen prüfen
echo ""
echo "Schritt 2: PHP-Erweiterungen prüfen"
echo "----------------------------------------"

required_extensions=("pdo" "pdo_mysql" "mbstring" "openssl" "json" "gd" "curl" "zip")

for ext in "${required_extensions[@]}"; do
    if php -m | grep -q "^$ext$"; then
        print_success "$ext installiert"
    else
        print_error "$ext NICHT installiert"
        missing_extensions=true
    fi
done

if [ "$missing_extensions" = true ]; then
    print_error "Fehlende PHP-Erweiterungen installieren und Script erneut ausführen"
    exit 1
fi

# Verzeichnisstruktur erstellen
echo ""
echo "Schritt 3: Verzeichnisstruktur einrichten"
echo "----------------------------------------"

# Ins api-Verzeichnis wechseln
if [ -d "api" ]; then
    cd api
    print_success "API-Verzeichnis gefunden"
else
    print_error "API-Verzeichnis nicht gefunden. Script aus webapp-Hauptverzeichnis ausführen."
    exit 1
fi

# Composer-Abhängigkeiten installieren
echo ""
echo "Schritt 4: Abhängigkeiten installieren"
echo "----------------------------------------"

if [ -f "composer.json" ]; then
    print_info "Composer-Abhängigkeiten werden installiert..."
    if composer install --no-dev --optimize-autoloader; then
        print_success "Composer-Abhängigkeiten installiert"
    else
        print_error "Composer-Installation fehlgeschlagen"
        exit 1
    fi
else
    print_error "composer.json nicht gefunden"
    exit 1
fi

# Zurück ins Hauptverzeichnis
cd ..

# Dateiberechtigungen setzen
echo ""
echo "Schritt 5: Dateiberechtigungen setzen"
echo "----------------------------------------"

# Verzeichnisse beschreibbar machen
directories=("api" "api/config" "api/utils")
for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
        chmod 755 "$dir"
        print_success "$dir Berechtigung: 755"
    fi
done

# PHP-Dateien ausführbar machen
find api -name "*.php" -exec chmod 644 {} \;
print_success "PHP-Dateien Berechtigung: 644"

# Datenbank-Konfiguration
echo ""
echo "Schritt 6: Datenbank-Konfiguration"
echo "----------------------------------------"

print_info "Konfigurieren Sie jetzt die Datenbankverbindung:"
print_info "1. Bearbeiten Sie: api/config/database.php"
print_info "2. Oder verwenden Sie unser interaktives Tool..."

read -p "Möchten Sie die Datenbank jetzt konfigurieren? (j/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[JjYy]$ ]]; then
    echo ""
    echo "Datenbankverbindung konfigurieren:"
    echo "-----------------------------------"
    
    read -p "MySQL Host (Standard: localhost): " db_host
    db_host=${db_host:-localhost}
    
    read -p "Datenbankname (Standard: schmitz_timesheet): " db_name
    db_name=${db_name:-schmitz_timesheet}
    
    read -p "MySQL Benutzername: " db_user
    
    read -s -p "MySQL Passwort: " db_pass
    echo ""
    
    # Backup der Original-Konfiguration
    cp api/config/database.php api/config/database.php.bak
    
    # Neue Konfiguration schreiben
    sed -i "s/private \$host = 'localhost';/private \$host = '$db_host';/" api/config/database.php
    sed -i "s/private \$database = 'schmitz_timesheet';/private \$database = '$db_name';/" api/config/database.php
    sed -i "s/private \$username = 'root';/private \$username = '$db_user';/" api/config/database.php
    sed -i "s/private \$password = '';/private \$password = '$db_pass';/" api/config/database.php
    
    print_success "Datenbankverbindung konfiguriert"
fi

# Webserver-Konfiguration
echo ""
echo "Schritt 7: Webserver-Konfiguration"
echo "----------------------------------------"

print_info "Webserver-Konfiguration:"

if command -v apache2 >/dev/null 2>&1 || command -v httpd >/dev/null 2>&1; then
    print_success "Apache erkannt"
    print_info "→ .htaccess bereits vorhanden"
    print_info "→ Stelle sicher, dass mod_rewrite aktiviert ist"
elif command -v nginx >/dev/null 2>&1; then
    print_success "Nginx erkannt"
    print_info "→ Verwende nginx.conf.example für Konfiguration"
    print_info "→ Kopiere die Konfiguration in deine Nginx-Config"
else
    print_warning "Webserver nicht automatisch erkannt"
fi

# Sicherheits-Check
echo ""
echo "Schritt 8: Sicherheits-Check"
echo "----------------------------------------"

# .htaccess prüfen
if [ -f ".htaccess" ]; then
    print_success ".htaccess gefunden"
else
    print_warning ".htaccess nicht gefunden - erstelle manuelle Webserver-Regeln"
fi

# Sensitive Dateien prüfen
sensitive_files=(".env" "config.php" "database.php")
for file in "${sensitive_files[@]}"; do
    if find . -name "$file" -type f 2>/dev/null | grep -q .; then
        print_warning "Sensitive Datei gefunden: $file - Webserver-Zugriff blockieren"
    fi
done

# Installation abschließen
echo ""
echo "========================================"
echo "Setup abgeschlossen!"
echo "========================================"

print_success "Grundlegende Installation erfolgreich"
print_info ""
print_info "Nächste Schritte:"
print_info "1. Webserver neustarten"
print_info "2. Browser öffnen: http://ihre-domain.de/api/install.php"
print_info "3. Installation abschließen"
print_info "4. Anmelden mit: admin@schmitz-intralogistik.de / admin123"
print_info "5. WICHTIG: install.php nach Installation löschen!"
print_info ""
print_info "Dokumentation:"
print_info "→ README.md - Übersicht"
print_info "→ INSTALLATION.md - Detaillierte Anleitung"
print_info "→ DATABASE_CONFIG.md - Datenbank-Konfiguration"
print_info ""

print_warning "Für Produktion:"
print_warning "→ HTTPS konfigurieren"
print_warning "→ Standard-Passwort ändern"
print_warning "→ Regelmäßige Backups einrichten"

echo ""
echo "🚀 Viel Erfolg mit Ihrer Zeiterfassung!"