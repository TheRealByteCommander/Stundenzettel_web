# Changelog - Schmitz Intralogistik Zeiterfassung

Alle wichtigen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

## [1.0.0] - 2025-01-31

### ✨ Neue Features
- **Komplette Webapplikation**: Vollständige Neuentwicklung als PHP/MySQL-Webapplikation
- **Benutzerauthentifizierung**: JWT-basierte Anmeldung mit Admin/User-Rollen
- **Wöchentliche Zeiterfassung**: Monday-only Datumsauswahl, 7-Tage-Eingabe
- **PDF-Generierung**: DIN A4 Querformat nach Corporate Design Template
- **E-Mail-Integration**: Automatischer PDF-Versand via SMTP-Konfiguration
- **Benutzerverwaltung**: Vollständige CRUD-Operationen mit Admin-Schutz
- **Status-Management**: Draft/Sent-Status für Timesheets mit Löschschutz
- **Corporate Design**: Schmitz Intralogistik Farben (#e90118, #b3b3b5, #5a5a5a)

### 🛠 Technische Implementierung
- **Frontend**: Vanilla JavaScript SPA mit Tailwind CSS
- **Backend**: PHP 7.4+ REST API mit PSR-4 Autoloading
- **Datenbank**: MySQL 5.7+ mit automatischer Schema-Erstellung
- **PDF**: DomPDF für serverseitige PDF-Generierung
- **E-Mail**: PHPMailer für SMTP-Integration
- **Authentifizierung**: Firebase JWT für sichere Token-Verwaltung

### 📁 Projektstruktur
```
webapp/
├── index.html                 # Single Page Application
├── assets/
│   ├── css/style.css         # Corporate Design
│   └── js/app.js             # Frontend Logic
├── api/                      # PHP Backend
│   ├── index.php             # API Router
│   ├── install.php           # Installations-Script
│   ├── composer.json         # Dependencies
│   ├── config/database.php   # DB-Konfiguration
│   ├── controllers/          # API Controllers
│   ├── middleware/           # JWT Middleware
│   └── utils/                # PDF & Email Services
├── .htaccess                 # Apache Configuration
└── nginx.conf.example        # Nginx Configuration
```

### 🔐 Sicherheitsfeatures
- **JWT-Authentifizierung**: Sichere Token-basierte Anmeldung
- **Admin-Schutz**: Letzter Admin nicht löschbar
- **Status-basierte Berechtigung**: Nur Draft-Timesheets löschbar
- **SQL-Injection-Schutz**: Prepared Statements
- **XSS-Schutz**: Input-Sanitization und Output-Escaping
- **CSRF-Schutz**: Token-basierte Requests

### 📊 Features im Detail

#### Benutzer-Features
- ✅ Wöchentliche Zeiterfassung (Mo-So)
- ✅ Monday-only Datumsauswahl
- ✅ Tägliche Eingabe: Start, Ende, Pause, Aufgaben, Ort, Projekt
- ✅ PDF-Download mit automatischem E-Mail-Versand
- ✅ Passwort selbst ändern
- ✅ Eigene Stundenzettel verwalten

#### Admin-Features
- ✅ Alle Benutzer verwalten (CRUD)
- ✅ Alle Stundenzettel einsehen und verwalten
- ✅ SMTP-Konfiguration für E-Mail-Versand
- ✅ Admin-Rechte vergeben/entziehen
- ✅ System-weite Statistiken

#### System-Features
- ✅ Automatische Gesamtstunden-Berechnung
- ✅ Kalenderwochen-Berechnung (ISO-Standard)
- ✅ Deutsche Lokalisierung
- ✅ Responsive Design (Mobile/Desktop)
- ✅ Automatische Datenbankinitialisierung
- ✅ Backup-Ready (MySQL-Export)

### 🎨 PDF-Template-Features
- **Format**: DIN A4 Querformat (Landscape)
- **Layout**: Professionelles Corporate Design
- **Inhalte**: 
  - Firmenkopf mit Logo und Adresse
  - Projekt/Kunde-Felder
  - 7-Tage-Tabelle (Montag-Sonntag)
  - Spalten: Datum, Startzeit, Endzeit, Pause, Beschreibung, Arbeitszeit
  - Automatische Gesamtstunden-Berechnung
  - Unterschriftsfelder (Mitarbeiter & Kunde)
- **Filename**: `{Mitarbeiter}_{KW}_{Nummer}.pdf`

### 📧 E-Mail-Features
- **SMTP-Support**: Konfigurierbar über Admin-Panel
- **Provider-Support**: Gmail, Outlook, eigene SMTP-Server
- **Automatischer Versand**: PDF-Anhang an Mitarbeiter + Admin
- **HTML-Templates**: Professionelle E-Mail-Vorlagen
- **Status-Update**: Timesheet wird auf "Sent" gesetzt

### 🚀 Installation & Deployment
- **Automatisches Setup**: `setup.sh` für Linux-Server
- **Web-Installer**: `install.php` für Browser-Installation
- **Webserver-Support**: Apache (.htaccess) + Nginx (config)
- **Hosting-Kompatibilität**: Shared Hosting bis VPS/Cloud
- **Standard-Admin**: admin@schmitz-intralogistik.de / admin123

### 📚 Dokumentation
- **README.md**: Projekt-Übersicht und Schnellstart
- **INSTALLATION.md**: Detaillierte Installationsanleitung
- **DATABASE_CONFIG.md**: Datenbank-Konfiguration für verschiedene Provider
- **Code-Kommentare**: Vollständig dokumentierter Quellcode

### 🔧 Konfigurierbarkeit
- **Datenbank**: Flexible MySQL-Konfiguration
- **E-Mail**: SMTP-Settings über Admin-Panel
- **Corporate Design**: Anpassbare Farben und Branding
- **PDF-Layout**: Template-basierte Anpassung möglich
- **Webserver**: Apache/Nginx-Konfigurationen

### 🐛 Bekannte Einschränkungen
- **Zeitzonenhandling**: Aktuell nur lokale Zeitzone
- **Mehrsprachigkeit**: Nur Deutsch implementiert
- **Erweiterte Berichte**: Aktuell nur PDF-Export
- **Mobile App**: Nur Web-basiert (PWA-ready)

### 🔄 Migration von vorherigen Versionen
Dies ist die erste Vollversion der Webapplikation. 
Migrationsskripte von anderen Systemen sind nicht enthalten.

## Roadmap für zukünftige Versionen

### [1.1.0] - Geplant
- **Erweiterte Berichte**: Excel-Export, Statistik-Dashboard
- **Zeitzonensupport**: Multi-Timezone-Unterstützung
- **PWA-Features**: Offline-Funktionalität
- **Erweiterte Sicherheit**: 2FA, Session-Management

### [1.2.0] - Geplant
- **Mehrsprachigkeit**: Englisch, weitere Sprachen
- **Advanced PDF**: Mehr Template-Optionen
- **API-Erweiterung**: RESTful API für Drittanbieter-Integration
- **Mobile Optimierung**: Native App-ähnliche Erfahrung

---

**Entwickelt für Schmitz Intralogistik GmbH**  
*Version 1.0.0 - Production Ready*