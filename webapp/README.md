# Schmitz Intralogistik GmbH - Zeiterfassung

Eine vollständige Webapplikation zur Zeiterfassung und Stundenzettel-Verwaltung.

## 🚀 Features

### ✅ Kompletter Funktionsumfang
- **Benutzerauthentifizierung**: JWT-basierte Anmeldung mit Admin/User-Rollen
- **Zeiterfassung**: Wöchentliche Stundenzettel mit Monday-only Datumsauswahl
- **PDF-Generierung**: DIN A4 Querformat nach Corporate Design Template
- **E-Mail-Versand**: Automatischer PDF-Versand via SMTP
- **Benutzerverwaltung**: CRUD-Operationen mit Admin-Schutz
- **Löschfunktionen**: Status-basierte Berechtigung (Draft/Sent)
- **Corporate Design**: Schmitz Intralogistik Farben und Branding

### 🛠 Technische Umsetzung
- **Frontend**: Vanilla JavaScript SPA mit Tailwind CSS
- **Backend**: PHP REST API mit JWT-Authentication
- **Datenbank**: MySQL mit automatischer Schema-Erstellung
- **PDF**: DomPDF für serverseitige PDF-Generierung
- **E-Mail**: PHPMailer für SMTP-Integration

## 📁 Projektstruktur

```
webapp/
├── index.html                 # Haupt-HTML-Datei (Single Page App)
├── assets/
│   ├── css/style.css         # Corporate Design Styling
│   └── js/app.js             # Frontend JavaScript (Vanilla JS)
├── api/                      # PHP Backend API
│   ├── index.php             # API Router
│   ├── install.php           # Installations-Script
│   ├── composer.json         # PHP Dependencies
│   ├── config/
│   │   └── database.php      # MySQL Datenbankverbindung
│   ├── controllers/          # API Controller
│   │   ├── AuthController.php
│   │   ├── UserController.php
│   │   ├── TimesheetController.php
│   │   └── AdminController.php
│   ├── middleware/
│   │   └── AuthMiddleware.php # JWT Authentication
│   └── utils/
│       ├── PDFGenerator.php  # PDF-Erstellung
│       └── EmailService.php  # E-Mail-Versand
├── .htaccess                 # Apache-Konfiguration
├── INSTALLATION.md           # Detaillierte Installationsanleitung
└── README.md                 # Diese Datei
```

## ⚡ Schnellstart

### 1. Dateien hochladen
Alle Dateien aus `webapp/` auf Ihren Webserver hochladen.

### 2. Datenbankverbindung konfigurieren
Bearbeiten Sie `api/config/database.php`:
```php
private $host = 'localhost';           // Ihr MySQL Host
private $database = 'schmitz_timesheet'; // Datenbankname  
private $username = 'ihr_db_user';        // MySQL Benutzername
private $password = 'ihr_db_passwort';    // MySQL Passwort
```

### 3. Installation ausführen
Öffnen Sie: `https://ihre-domain.de/api/install.php`

### 4. Anmelden
- **E-Mail**: admin@schmitz-intralogistik.de
- **Passwort**: admin123

### 5. Sicherheit
**Wichtig:** Löschen Sie nach Installation `api/install.php`!

## 📋 Systemanforderungen

### Server
- PHP 7.4+ (empfohlen: PHP 8.0+)
- MySQL 5.7+ / MariaDB 10.2+
- Apache 2.4+ / Nginx 1.18+
- Composer

### PHP-Erweiterungen
```
pdo, pdo_mysql, mbstring, openssl, json, gd, curl, zip
```

## 🔧 Konfiguration

### SMTP für E-Mails (im Admin-Panel)
```
Gmail:
- Server: smtp.gmail.com
- Port: 587
- Benutzer: ihre-email@gmail.com
- Passwort: ihr-app-passwort

Outlook/Microsoft 365:
- Server: smtp-mail.outlook.com  
- Port: 587
- Benutzer: ihre-email@outlook.com
- Passwort: ihr-passwort

Eigener Server:
- Server: mail.ihre-domain.de
- Port: 587
- Benutzer: noreply@ihre-domain.de
- Passwort: ihr-mail-passwort
```

## 🔒 Sicherheit

### Produktionsumgebung
- [ ] HTTPS aktivieren (SSL-Zertifikat)
- [ ] Standard-Admin-Passwort ändern
- [ ] `install.php` löschen
- [ ] Starke Datenbankpasswörter verwenden
- [ ] Regelmäßige Backups einrichten
- [ ] PHP und Dependencies aktuell halten

### Backup
```bash
# Datenbank-Backup
mysqldump -u username -p schmitz_timesheet > backup.sql

# Dateien-Backup  
tar -czf webapp_backup.tar.gz webapp/
```

## 🎨 Corporate Design

### Farben
- **Primary Red**: #e90118
- **Light Gray**: #b3b3b5  
- **Dark Gray**: #5a5a5a

### PDF-Layout
- DIN A4 Querformat
- Deutsche Wochentage (Montag-Sonntag)
- Firmenlogo und Adresse
- Projekt/Kunde Felder
- Unterschriftsfelder

## 📊 Funktionsübersicht

### Benutzer-Features
- ✅ Wöchentliche Zeiterfassung
- ✅ Monday-only Datumsauswahl
- ✅ PDF-Download mit automatischem E-Mail-Versand
- ✅ Passwort ändern
- ✅ Eigene Stundenzettel verwalten

### Admin-Features  
- ✅ Alle Benutzer und Stundenzettel verwalten
- ✅ SMTP-Konfiguration
- ✅ Benutzer anlegen/bearbeiten/löschen
- ✅ Admin-Schutz (letzter Admin nicht löschbar)
- ✅ Vollzugriff auf alle Timesheets

### System-Features
- ✅ JWT-basierte Authentifizierung
- ✅ Status-Management (Draft/Sent)
- ✅ Automatische Datenbankinitialisierung
- ✅ Responsive Design (Mobile/Desktop)
- ✅ Webserver-kompatibel (Apache/Nginx)

## 🐛 Fehlerbehebung

### Häufige Probleme

**"Database connection failed"**
→ Überprüfen Sie `api/config/database.php`

**"Composer not found"**  
→ Composer installieren oder manuell: `cd api && composer install`

**"PDF generation failed"**
→ PHP-GD-Erweiterung installieren, memory_limit erhöhen

**"Email sending failed"**
→ SMTP-Konfiguration und Firewall-Einstellungen prüfen

### Debug-Modus
In `api/index.php` hinzufügen:
```php
error_reporting(E_ALL);
ini_set('display_errors', 1);
```

## 📚 Dokumentation

- **[INSTALLATION.md](INSTALLATION.md)**: Detaillierte Installationsanleitung
- **API-Dokumentation**: Alle Endpunkte in `api/index.php`
- **Frontend-Code**: Dokumentiert in `assets/js/app.js`

## 🔄 Updates

### Composer-Dependencies aktualisieren
```bash
cd api/
composer update
```

### Manuelle Updates
1. Backup erstellen
2. Neue Dateien hochladen  
3. `composer install` ausführen
4. Datenbank-Schema überprüfen

## 📞 Support

Bei Problemen:
1. Systemanforderungen überprüfen
2. Webserver-Logs kontrollieren
3. Datenbankverbindung testen
4. `INSTALLATION.md` konsultieren

---

**Entwickelt für Schmitz Intralogistik GmbH**  
*Professional Timesheet Management System*