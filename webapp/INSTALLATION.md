# Schmitz Intralogistik GmbH - Zeiterfassung Installation

## Systemanforderungen

### Server-Anforderungen
- **PHP**: Version 7.4 oder höher
- **MySQL**: Version 5.7 oder höher (oder MariaDB 10.2+)
- **Webserver**: Apache 2.4+ oder Nginx 1.18+
- **Composer**: Für Dependency Management

### PHP-Erweiterungen
Stellen Sie sicher, dass folgende PHP-Erweiterungen installiert sind:
```
- pdo
- pdo_mysql
- mbstring
- openssl
- json
- gd (für PDF-Generierung)
- curl
- zip
```

## Installation

### Schritt 1: Dateien hochladen
Laden Sie alle Dateien aus dem `webapp/` Ordner auf Ihren Webserver hoch.

### Schritt 2: Datenbankverbindung konfigurieren
Bearbeiten Sie die Datei `api/config/database.php`:

```php
<?php
class Database {
    private $host = 'localhost';           // Ihr MySQL Host
    private $database = 'schmitz_timesheet'; // Datenbankname
    private $username = 'ihr_db_user';        // MySQL Benutzername
    private $password = 'ihr_db_passwort';    // MySQL Passwort
    
    // ... Rest der Klasse bleibt unverändert
}
?>
```

### Schritt 3: Installation ausführen
Öffnen Sie in Ihrem Browser: `https://ihre-domain.de/api/install.php`

Das Installationsskript wird automatisch:
- PHP-Abhängigkeiten installieren (Composer)
- Datenbank und Tabellen erstellen
- Standard-Admin-Account anlegen
- System-Checks durchführen

### Schritt 4: Sicherheit
**Wichtig:** Löschen Sie nach erfolgreicher Installation die Datei `api/install.php`!

```bash
rm api/install.php
```

## Datenbank-Konfiguration

### Option 1: Automatische Erstellung
Das Installationsskript erstellt automatisch:
- Datenbank `schmitz_timesheet`
- Alle erforderlichen Tabellen
- Standard-Admin-Account

### Option 2: Manuelle Erstellung
Falls Sie die Datenbank manuell erstellen möchten:

```sql
-- Datenbank erstellen
CREATE DATABASE schmitz_timesheet CHARACTER SET utf8 COLLATE utf8_general_ci;

-- Benutzer-Tabelle
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Stundenzettel-Tabelle
CREATE TABLE timesheets (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    user_name VARCHAR(255) NOT NULL,
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    entries JSON NOT NULL,
    status ENUM('draft', 'sent') DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- SMTP-Konfiguration-Tabelle
CREATE TABLE smtp_config (
    id VARCHAR(36) PRIMARY KEY,
    smtp_server VARCHAR(255) NOT NULL,
    smtp_port INT NOT NULL DEFAULT 587,
    smtp_username VARCHAR(255) NOT NULL,
    smtp_password VARCHAR(255) NOT NULL,
    admin_email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Standard-Admin-Account erstellen
INSERT INTO users (id, email, name, password_hash, is_admin) VALUES (
    UUID(),
    'admin@schmitz-intralogistik.de',
    'Administrator',
    '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', -- admin123
    TRUE
);
```

## Webserver-Konfiguration

### Apache
Stellen Sie sicher, dass `.htaccess` unterstützt wird:
```apache
# In der Apache-Konfiguration oder .htaccess
AllowOverride All

# Mod_rewrite aktivieren
LoadModule rewrite_module modules/mod_rewrite.so
```

### Nginx
Beispiel-Konfiguration:
```nginx
server {
    listen 80;
    server_name ihre-domain.de;
    root /pfad/zu/webapp;
    index index.html;

    # API Routes
    location /api/ {
        try_files $uri $uri/ /api/index.php?$query_string;
    }

    # PHP handling
    location ~ \.php$ {
        fastcgi_pass unix:/var/run/php/php7.4-fpm.sock;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }

    # Single Page App
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
}
```

## Standard-Anmeldedaten

Nach der Installation können Sie sich mit folgenden Daten anmelden:
- **E-Mail**: admin@schmitz-intralogistik.de
- **Passwort**: admin123

**Wichtig:** Ändern Sie das Standard-Passwort sofort nach der ersten Anmeldung!

## SMTP-Konfiguration für E-Mails

### Gmail (Beispiel)
```
SMTP Server: smtp.gmail.com
SMTP Port: 587
Benutzername: ihre-email@gmail.com
Passwort: ihr-app-passwort
Admin E-Mail: admin@schmitz-intralogistik.de
```

### Microsoft 365/Outlook
```
SMTP Server: smtp-mail.outlook.com
SMTP Port: 587
Benutzername: ihre-email@outlook.com
Passwort: ihr-passwort
Admin E-Mail: admin@schmitz-intralogistik.de
```

### Eigener Mail-Server
```
SMTP Server: mail.ihre-domain.de
SMTP Port: 587 (oder 25, 465)
Benutzername: noreply@ihre-domain.de
Passwort: ihr-mail-passwort
Admin E-Mail: admin@ihre-domain.de
```

## Fehlerbehebung

### Häufige Probleme

**Problem: "Database connection failed"**
```
Lösung: Überprüfen Sie die Datenbankverbindung in api/config/database.php
- Host-Adresse korrekt?
- Benutzername/Passwort korrekt?
- Datenbank existiert?
```

**Problem: "Composer not found"**
```
Lösung: Installieren Sie Composer oder führen Sie manuell aus:
cd api/
composer install
```

**Problem: "PDF generation failed"**
```
Lösung: Überprüfen Sie PHP-Erweiterungen:
- php-gd installiert?
- Ausreichend memory_limit? (empfohlen: 256M)
```

**Problem: "Email sending failed"**
```
Lösung: SMTP-Konfiguration überprüfen:
- Korrekte Server-Daten?
- Firewall blockiert Port 587?
- 2FA/App-Passwort bei Gmail erforderlich?
```

### Debug-Modus aktivieren
Für Entwicklung/Debugging in `api/index.php` hinzufügen:
```php
// Am Anfang der Datei
error_reporting(E_ALL);
ini_set('display_errors', 1);
```

### Log-Dateien
PHP-Logs finden Sie normalerweise unter:
- `/var/log/apache2/error.log` (Apache)
- `/var/log/nginx/error.log` (Nginx)
- `/var/log/php7.4-fpm.log` (PHP-FPM)

## Support

Bei Problemen:
1. Überprüfen Sie die Systemanforderungen
2. Kontrollieren Sie die Webserver-Logs
3. Testen Sie die Datenbankverbindung
4. Überprüfen Sie Dateiberechtigungen

## Sicherheitshinweise

### Produktion
- HTTPS verwenden (SSL-Zertifikat)
- Starke Passwörter verwenden
- Regelmäßige Backups erstellen
- PHP und alle Abhängigkeiten aktuell halten
- `install.php` nach Installation löschen

### Backup
Wichtige Dateien für Backup:
- Gesamter `webapp/` Ordner
- MySQL-Datenbank `schmitz_timesheet`
- Webserver-Konfiguration

```bash
# Datenbank-Backup
mysqldump -u username -p schmitz_timesheet > backup_$(date +%Y%m%d).sql

# Dateien-Backup
tar -czf webapp_backup_$(date +%Y%m%d).tar.gz webapp/
```