# Stundenzettel Web - Zeiterfassungssystem

Web-basiertes Zeiterfassungssystem für Schmitz Intralogistik GmbH.

## Features

### Stundenzettel-App
- ✅ Wochenbasierte Zeiterfassung
- ✅ PDF-Generierung für Stundenzettel
- ✅ E-Mail-Versand mit PDF-Anhang
- ✅ Urlaub, Krankheit, Feiertag-Tracking
- ✅ Fahrzeit-Erfassung mit optionaler Weiterberechnung
- ✅ Monatsstatistiken und Rang-System
- ✅ Stundenzettel-Genehmigung durch Buchhaltung

### Reisekosten-App
- ✅ Automatische Befüllung aus genehmigten Stundenzetteln
- ✅ PDF-Beleg-Upload (lokale Speicherung, DSGVO-konform)
- ✅ Monatsbasierte Abrechnungen (aktueller + 2 Monate zurück)
- ✅ Chat-System für Rückfragen mit Agenten
- ✅ Status-Management (Entwurf, In Prüfung, Genehmigt)
- ✅ Automatische Prüfung mit Ollama LLM-Agenten
  - Dokumentenanalyse (OCR, Kategorisierung, Validierung)
  - Buchhaltungszuordnung (Verpflegungsmehraufwand, Spesensätze)
  - Chat-Agent für Rückfragen

### Weitere Features
- ✅ Benutzer- und Adminverwaltung mit Rollen (User, Admin, Buchhaltung)
- ✅ Obligatorische 2FA (Google Authenticator)
- ✅ Ankündigungen/News-System mit Bildern
- ✅ Mobile-First Responsive Web-Interface
- ✅ PWA-Support (Installierbar auf Mobilgeräten)
- ✅ DSGVO & EU-AI-Act Compliance
  - Datenverschlüsselung (Fernet/AES-128)
  - Audit-Logging
  - Retention-Management
  - AI-Transparenz
- ✅ Datenbank-Migrations-Tool (Import aus Vorgänger-Version)
- ✅ LLM-Integration für Proxmox (Agents auf Proxmox, LLMs auf GMKTec evo x2)

## 📘 Installationsanleitungen

**Wichtiger Hinweis:** Diese Anwendung läuft auf einem All-inkl.com Webserver.

- **Für All-inkl.com:** Siehe **[INSTALLATION_ALL_INKL.md](INSTALLATION_ALL_INKL.md)** - Vollständige, spezifische Anleitung
- **Für andere Server:** Siehe **[INSTALLATION_COMPLETE.md](INSTALLATION_COMPLETE.md)** - Allgemeine Installationsanleitung
- **Schnellstart:** Siehe **[QUICK_START.md](QUICK_START.md)**

## Installation auf All-Inkl.com Webserver (Kurzanleitung)

### Voraussetzungen

- All-Inkl.com Hosting-Paket mit PHP 7.4+ und MySQL
- FTP/SFTP-Zugang zum Webserver
- Datenbank-Zugangsdaten aus dem All-Inkl Control Panel

### Schritt 1: Datenbank erstellen

1. Loggen Sie sich in Ihr **All-Inkl Kundenmenü** ein
2. Navigieren Sie zu **"Datenbanken"** oder **"MySQL-Datenbanken"**
3. Erstellen Sie eine neue MySQL-Datenbank:
   - Datenbankname: z.B. `kXXXXXX_stundenzettel` (wird automatisch mit Ihrem Kürzel ergänzt)
   - Notieren Sie sich den vollständigen Datenbanknamen
4. Erstellen Sie einen Datenbankbenutzer:
   - Benutzername: z.B. `kXXXXXX_user` (ebenfalls mit Kürzel)
   - Passwort: starkes Passwort generieren
   - Benutzer der Datenbank zuordnen

### Schritt 2: Frontend-Dateien hochladen

1. Öffnen Sie einen **FTP-Client** (z.B. FileZilla)
2. Verbinden Sie sich mit Ihrem All-Inkl-Server:
   - **Host**: `ftp.kasserver.com` oder die IP aus dem Kundenmenü
   - **Benutzername**: Ihr All-Inkl-Kürzel (z.B. k123456)
   - **Passwort**: Ihr FTP-Passwort
   - **Port**: 21 (FTP) oder 22 (SFTP)
3. Navigieren Sie zum **öffentlichen Web-Verzeichnis**:
   - Meist: `/html/` oder `/www/` oder `/`
4. Laden Sie den gesamten **`frontend/`** Ordner hoch
5. Optional: Benennen Sie den Ordner um (z.B. `zeiterfassung`)

**Wichtig:** Stellen Sie sicher, dass die `build/` Dateien aus dem Frontend-Build-Prozess hochgeladen werden (siehe Schritt 3).

### Schritt 3: Frontend bauen

Lokal auf Ihrem Computer:

```bash
cd frontend/
npm install
# oder
yarn install

# Erstellen Sie eine .env Datei mit:
REACT_APP_BACKEND_URL=https://ihre-domain.de/api

# Build erstellen
npm run build
# oder
yarn build
```

Laden Sie dann den Inhalt des **`frontend/build/`** Ordners ins Web-Verzeichnis hoch.

### Schritt 4: Backend-Dateien hochladen

1. Laden Sie den **`backend/`** Ordner auf den Server hoch
2. Empfohlener Ort: **außerhalb des öffentlichen Web-Verzeichnisses** (z.B. `/private/backend/`)
3. Alternativ: In einen **geschützten Ordner** innerhalb des Web-Verzeichnisses (z.B. `/html/api/`)

### Schritt 5: Backend-Umgebung konfigurieren

1. Erstellen Sie eine **`.env`** Datei im `backend/` Ordner:

```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=stundenzettel
SECRET_KEY=ihr-sehr-geheimes-secret-key-min-32-zeichen
```

**Wichtig für All-Inkl:**
- Falls MongoDB nicht verfügbar ist, müssen Sie die MySQL/PHP-Version verwenden (siehe `webapp/` Ordner)
- All-Inkl bietet normalerweise **nur MySQL**, nicht MongoDB

### Schritt 6: PHP-Version (Alternative zu Python Backend)

Da All-Inkl.com in der Regel **keine Python-Umgebung** bietet, verwenden Sie bitte die **PHP-Implementation** aus dem `webapp/` Ordner:

1. Laden Sie den **`webapp/`** Ordner ins Web-Verzeichnis hoch (z.B. `/html/api/`)
2. Navigieren Sie zu: **All-Inkl Kundenmenü → PHP-Einstellungen**
3. Stellen Sie sicher, dass **PHP 7.4 oder höher** aktiviert ist
4. Aktivieren Sie folgende PHP-Erweiterungen (falls verfügbar):
   - `pdo`
   - `pdo_mysql`
   - `mbstring`
   - `openssl`
   - `json`
   - `gd`
   - `curl`
   - `zip`

### Schritt 7: Datenbank-Konfiguration (PHP-Version)

1. Bearbeiten Sie `webapp/api/config/database.php`:

```php
<?php
class Database {
    // All-Inkl Datenbankdetails
    private $host = 'localhost';  // Meistens localhost bei All-Inkl
    private $database = 'kXXXXXX_stundenzettel';  // Ihr vollständiger DB-Name
    private $username = 'kXXXXXX_user';  // Ihr vollständiger DB-User
    private $password = 'ihr-db-passwort';  // Ihr DB-Passwort
    
    // ... Rest bleibt gleich
}
?>
```

2. Stellen Sie sicher, dass die Dateiberechtigungen korrekt sind (meist 644 für Dateien, 755 für Ordner)

### Schritt 8: Installation ausführen

1. Öffnen Sie in Ihrem Browser:
   ```
   https://ihre-domain.de/api/install.php
   ```
2. Das Installationsskript führt automatisch aus:
  ⬜ Datenbank-Tabellen erstellen
   - Standard-Admin-Account anlegen
   - System-Checks durchführen

### Schritt 9: Frontend mit Backend verbinden

1. Erstellen/bearbeiten Sie `frontend/.env` oder setzen Sie die Umgebungsvariable:
   ```
   REACT_APP_BACKEND_URL=https://ihre-domain.de/api
   ```
2. Builden Sie das Frontend neu (siehe Schritt 3)

### Schritt 10: .htaccess konfigurieren (Apache)

All-Inkl verwendet meist Apache. Erstellen Sie eine `.htaccess` Datei im Root-Verzeichnis:

```apache
# PHP-Version setzen
AddHandler application/x-httpd-php74 .php

# URL-Rewriting für API
RewriteEngine On
RewriteBase /

# API-Routes weiterleiten
RewriteRule ^api/(.*)$ api/index.php [QSA,L]

# Frontend-Routes (React Router)
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^ index.html [L]

# Sicherheit
<Files "config/database.php">
    Order allow,deny
    Deny from all
</Files>
```

### Schritt 11: Sicherheitseinstellungen

1. **Installationsskript löschen** (nach erfolgreicher Installation):
   ```bash
   # Via FTP: Löschen Sie api/install.php
   ```

2. **Dateiberechtigungen setzen**:
   - Ordner: 755
   - Dateien: 644
   - Konfigurationsdateien: 600 (falls möglich)

3. **HTTPS aktivieren**:
   - All-Inkl bietet kostenlose SSL-Zertifikate (Let's Encrypt)
   - Aktivieren Sie HTTPS im Kundenmenü

### Schritt 12: SMTP-Konfiguration

1. Loggen Sie sich in die Anwendung ein (Standard: `admin@schmitz-intralogistik.de` / `admin123`)
2. Gehen Sie zu **Admin → SMTP Konfiguration**
3. Verwenden Sie All-Inkl Mail-Server:
   ```
   SMTP Server: mail.kasserver.com
   SMTP Port: 587
   Benutzername: ihre-email@ihre-domain.de
   Passwort: ihr-email-passwort
   Admin E-Mail: admin@ihre-domain.de
   ```

### All-Inkl spezifische Hinweise

- **Datenbank-Hostname**: Meist `localhost` (nicht die externe IP)
- **MySQL-Socket**: Falls `localhost` nicht funktioniert, versuchen Sie `127.0.0.1`
- **Datei-Upload-Limit**: Standard sind meist 10-50MB (ausreichend für PDFs)
- **PHP Memory Limit**: Kann über `.htaccess` erhöht werden:
  ```apache
  php_value memory_limit 256M
  ```
- **Cronjobs**: Für regelmäßige Backups können Sie Cronjobs im All-Inkl Kundenmenü einrichten

### Fehlerbehebung bei All-Inkl

**Problem: "Datenbankverbindung fehlgeschlagen"**
- Überprüfen Sie, ob der Datenbankname das korrekte Kürzel enthält
- Hostname sollte `localhost` sein, nicht die externe IP
- MySQL-Socket könnte erforderlich sein

**Problem: "Composer nicht gefunden"**
- All-Inkl bietet meist kein CLI-Zugang
- Laden Sie die `vendor/` Ordner manuell hoch oder verwenden Sie den Composer-Autoloader lokal

**Problem: "403 Forbidden" bei API-Aufrufen**
- Überprüfen Sie `.htaccess` Datei
- Stellen Sie sicher, dass `mod_rewrite` aktiviert ist
- Kontaktieren Sie All-Inkl Support bei Problemen

**Problem: "CORS-Fehler"**
- API muss CORS-Header senden
- Überprüfen Sie Backend-CORS-Konfiguration
- Falls nötig, fügen Sie Header in `.htaccess` hinzu:
  ```apache
  Header set Access-Control-Allow-Origin "*"
  Header set Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS"
  Header set Access-Control-Allow-Headers "Content-Type, Authorization"
  ```

## Standard-Anmeldedaten

Nach der Installation:
- **E-Mail**: admin@schmitz-intralogistik.de
- **Passwort**: admin123

**⚠️ Wichtig:** Ändern Sie das Passwort sofort nach der ersten Anmeldung!

## Support

Bei Problemen:
1. Überprüfen Sie die PHP-Version (All-Inkl Kundenmenü → PHP-Einstellungen)
2. Kontrollieren Sie die Datenbankverbindung
3. Überprüfen Sie Dateiberechtigungen
4. Kontaktieren Sie bei Bedarf den All-Inkl Support

## Konfiguration für Reisekosten-App

### Lokaler Speicherpfad für Belege

Die Reisekosten-App speichert PDF-Belege **nicht auf dem Webserver**, sondern auf einem lokalen Bürorechner.

Konfigurieren Sie den Pfad in der `.env` Datei des Backends:

```env
LOCAL_RECEIPTS_PATH=C:/Reisekosten_Belege
```

**Wichtig:** 
- Dieser Pfad muss auf dem Rechner existieren, auf dem der Backend-Server läuft
- Der Server benötigt Schreibrechte auf diesem Verzeichnis
- Unter Windows: Verwenden Sie absolute Pfade mit Laufwerksbuchstaben (z.B. `C:/Reisekosten_Belege`)
- Unter Linux: Verwenden Sie absolute Pfade (z.B. `/var/receipts`)

### Ollama LLM Integration

Für die automatische Prüfung von Reisekostenabrechnungen:

**Architektur:**
- Agents laufen auf Proxmox-Server
- LLMs laufen auf GMKTec evo x2 Rechner im lokalen Netzwerk

**Konfiguration:**
```env
OLLAMA_BASE_URL=http://192.168.1.100:11434  # IP des GMKTec-Servers
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=300
OLLAMA_MAX_RETRIES=3
```

Siehe **[backend/LLM_INTEGRATION.md](backend/LLM_INTEGRATION.md)** für Details.

## 📚 Weitere Dokumentation

- **Installationsanleitungen:**
  - [INSTALLATION_ALL_INKL.md](INSTALLATION_ALL_INKL.md) - All-inkl.com spezifisch
  - [INSTALLATION_COMPLETE.md](INSTALLATION_COMPLETE.md) - Allgemeine Installation
  - [QUICK_START.md](QUICK_START.md) - Schnellstart

- **Feature-Dokumentation:**
  - [backend/AGENTS_README.md](backend/AGENTS_README.md) - Agent-Netzwerk
  - [backend/LLM_INTEGRATION.md](backend/LLM_INTEGRATION.md) - LLM-Integration (Proxmox/GMKTec)
  - [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Datenbank-Migration
  - [backend/MIGRATION_README.md](backend/MIGRATION_README.md) - Migration API
  - [backend/DSGVO_COMPLIANCE.md](backend/DSGVO_COMPLIANCE.md) - DSGVO & EU-AI-Act
  - [frontend/src/SECURITY.md](frontend/src/SECURITY.md) - Frontend-Sicherheit

- **Änderungshistorie:** Siehe [CHANGELOG.md](CHANGELOG.md)
