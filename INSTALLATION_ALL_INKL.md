# 📘 Installationsanleitung für All-inkl.com
## Stundenzettel Web - Zeiterfassungssystem für Schmitz Intralogistik GmbH

**Spezielle Anleitung für All-inkl.com Shared Hosting**

---

## 📋 Inhaltsverzeichnis

1. [Voraussetzungen](#voraussetzungen)
2. [Installation Schritt für Schritt](#installation-schritt-für-schritt)
3. [Datenbank einrichten](#datenbank-einrichten)
4. [Dateien hochladen](#dateien-hochladen)
5. [Konfiguration](#konfiguration)
6. [Installation ausführen](#installation-ausführen)
7. [SMTP konfigurieren](#smtp-konfigurieren)
8. [SSL/HTTPS einrichten](#sslhttps-einrichten)
9. [Fehlerbehebung](#fehlerbehebung)
10. [Wartung & Updates](#wartung--updates)

---

## 🔧 Voraussetzungen

### All-inkl.com Account-Anforderungen

- ✅ **All-inkl.com Hosting-Paket** (Home, Business oder höher)
- ✅ **FTP/SFTP-Zugang** zum Webserver
- ✅ **MySQL-Datenbank** (im Paket enthalten)
- ✅ **PHP 7.4 oder höher** (meist bereits aktiviert)
- ✅ **Zugriff auf Kundenmenü** (https://kis.all-inkl.com)

### Technische Voraussetzungen

- **PHP Version:** 7.4 oder höher (8.0+ empfohlen)
- **MySQL Version:** 5.7 oder höher (8.0 empfohlen)
- **PHP Extensions erforderlich:**
  - `pdo`
  - `pdo_mysql`
  - `mbstring`
  - `openssl`
  - `json`
  - `gd`
  - `curl`
  - `zip`
  - `fileinfo`

**Hinweis:** All-inkl.com bietet **keine Python-Umgebung**, daher wird die **PHP-Version** aus dem `webapp/` Ordner verwendet.

---

## 📦 Installation Schritt für Schritt

### Schritt 1: Datenbank erstellen

1. **Loggen Sie sich ins All-inkl Kundenmenü ein:**
   - URL: https://kis.all-inkl.com
   - Benutzername: Ihr All-inkl Kürzel (z.B. k123456)
   - Passwort: Ihr Kundenmenü-Passwort

2. **Navigieren Sie zu "Datenbanken":**
   - Im Hauptmenü: **"Datenbanken"** → **"MySQL-Datenbanken"**
   - Oder direkter Link: Datenbanken-Verwaltung

3. **Neue Datenbank erstellen:**
   - Klicken Sie auf **"Neue MySQL-Datenbank erstellen"**
   - **Datenbankname:** z.B. `stundenzettel`
     - ⚠️ **WICHTIG:** All-inkl fügt automatisch Ihr Kürzel voran!
     - Vollständiger Name wird: `kXXXXXX_stundenzettel`
   - Notieren Sie sich den **vollständigen Datenbanknamen**

4. **Datenbankbenutzer erstellen:**
   - **Neuen MySQL-Benutzer erstellen**
   - **Benutzername:** z.B. `stundenzettel_user`
     - Vollständiger Name: `kXXXXXX_stundenzettel_user`
   - **Passwort:** Starkes Passwort generieren (mindestens 16 Zeichen)
     - ✅ Verwenden Sie Groß- und Kleinbuchstaben, Zahlen, Sonderzeichen
   - **Benutzer der Datenbank zuordnen**
   - ✅ Notieren Sie sich alle Daten:
     - Datenbankname (vollständig mit Kürzel)
     - Benutzername (vollständig mit Kürzel)
     - Passwort

5. **Datenbank-Verbindung testen (optional):**
   - In All-inkl Kundenmenü: **phpMyAdmin** öffnen
   - Mit den erstellten Zugangsdaten einloggen
   - Überprüfen Sie, dass die Datenbank sichtbar ist

---

### Schritt 2: PHP-Version prüfen und aktivieren

1. **Im All-inkl Kundenmenü:**
   - Navigieren Sie zu **"Einstellungen"** → **"PHP-Einstellungen"**
   - Oder: **"Kundenmenü"** → **"PHP"**

2. **PHP-Version wählen:**
   - ✅ **PHP 7.4 oder höher** wählen (PHP 8.0+ empfohlen)
   - Für Ihr Domain oder Verzeichnis aktivieren

3. **PHP-Extensions prüfen:**
   - In PHP-Einstellungen können Sie meist Extensions aktivieren/deaktivieren
   - Stellen Sie sicher, dass folgende aktiviert sind:
     - ✅ `pdo`
     - ✅ `pdo_mysql`
     - ✅ `mbstring`
     - ✅ `openssl`
     - ✅ `json`
     - ✅ `gd`
     - ✅ `curl`
     - ✅ `zip`

4. **PHP-Info prüfen (optional):**
   - Erstellen Sie eine `phpinfo.php` Datei:
     ```php
     <?php phpinfo(); ?>
     ```
   - Laden Sie sie hoch und öffnen Sie sie im Browser
   - Überprüfen Sie die aktive PHP-Version und Extensions

---

### Schritt 3: FTP-Zugang einrichten

1. **FTP-Zugangsdaten notieren:**
   - **Host:** Meist `ftp.kasserver.com` oder Ihre Domain
   - **Port:** 21 (FTP) oder 22 (SFTP) - **SFTP empfohlen!**
   - **Benutzername:** Ihr All-inkl Kürzel (z.B. k123456)
   - **Passwort:** Ihr FTP-Passwort (kann im Kundenmenü geändert werden)

2. **FTP-Client installieren (falls nicht vorhanden):**
   - **FileZilla** (empfohlen, kostenlos): https://filezilla-project.org/
   - **WinSCP** (Windows): https://winscp.net/
   - **Cyberduck** (Mac): https://cyberduck.io/

3. **FTP-Verbindung testen:**
   - Verbinden Sie sich mit Ihrem FTP-Client
   - Navigieren Sie zum **Web-Verzeichnis**
     - Meist: `/html/` oder `/www/` oder `/`
     - Oder: `/kunden/kXXXXXX/stundenzettel_web/`
     - Der genaue Pfad steht im All-inkl Kundenmenü

---

### Schritt 4: Dateien vorbereiten (lokal)

1. **Repository herunterladen:**
   ```bash
   git clone https://github.com/TheRealByteCommander/Stundenzettel_web.git
   cd Stundenzettel_web
   ```

2. **Oder ZIP-Datei herunterladen:**
   - Von GitHub: Code → Download ZIP
   - ZIP-Datei entpacken

3. **PHP-Version auswählen:**
   - Navigieren Sie zum **`webapp/`** Ordner
   - Dieser enthält die PHP-Version für All-inkl

---

### Schritt 5: Backend-Dateien hochladen

1. **Ordnerstruktur vorbereiten:**
   - Erstellen Sie einen Ordner für die API (z.B. `api` oder `backend`)
   - Empfehlung: `/html/api/` oder `/html/stundenzettel/api/`

2. **Dateien hochladen:**
   - Kopieren Sie den gesamten Inhalt von `webapp/api/` auf den Server
   - Struktur auf Server sollte sein:
     ```
     /html/api/
     ├── index.php
     ├── install.php
     ├── config/
     │   └── database.php
     ├── controllers/
     │   ├── AuthController.php
     │   ├── UserController.php
     │   ├── TimesheetController.php
     │   └── AdminController.php
     ├── middleware/
     │   └── AuthMiddleware.php
     ├── utils/
     │   ├── PDFGenerator.php
     │   ├── EmailService.php
     │   └── SimpleJWT.php
     └── utils/tcpdf/
         └── [alle TCPDF-Dateien]
     ```

3. **Dateiberechtigungen setzen:**
   - **Ordner:** 755
   - **Dateien:** 644
   - **Konfigurationsdateien:** 600 (falls möglich)
   - Meist automatisch korrekt, aber überprüfen

---

### Schritt 6: Datenbank-Konfiguration

1. **`config/database.php` bearbeiten:**
   
   Öffnen Sie die Datei auf dem Server via FTP-Editor oder lokal bearbeiten und hochladen:

   ```php
   <?php
   class Database {
       // All-inkl Datenbankdetails
       private $host = 'localhost';  // Meist localhost bei All-inkl
       private $database = 'kXXXXXX_stundenzettel';  // Ihr vollständiger DB-Name MIT Kürzel
       private $username = 'kXXXXXX_stundenzettel_user';  // Ihr vollständiger DB-User MIT Kürzel
       private $password = 'Ihr-Datenbank-Passwort';  // Ihr DB-Passwort
       
       private $connection = null;
       
       public function getConnection() {
           if ($this->connection === null) {
               try {
                   $dsn = "mysql:host={$this->host};dbname={$this->database};charset=utf8mb4";
                   $options = [
                       PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                       PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                       PDO::ATTR_EMULATE_PREPARES => false,
                   ];
                   $this->connection = new PDO($dsn, $this->username, $this->password, $options);
               } catch (PDOException $e) {
                   error_log("Database connection error: " . $e->getMessage());
                   throw new Exception("Datenbankverbindung fehlgeschlagen");
               }
           }
           return $this->connection;
       }
   }
   ?>
   ```

2. **WICHTIG - Kürzel nicht vergessen:**
   - All-inkl fügt automatisch Ihr Kürzel (z.B. `k123456`) voran
   - Datenbankname in All-inkl: `stundenzettel` → Vollständig: `k123456_stundenzettel`
   - Benutzername in All-inkl: `stundenzettel_user` → Vollständig: `k123456_stundenzettel_user`

3. **Hostname prüfen:**
   - Meist: `localhost`
   - Falls nicht: Versuchen Sie `127.0.0.1`
   - In seltenen Fällen: `mysql.kasserver.com` (siehe All-inkl Dokumentation)

---

### Schritt 7: Installation ausführen

1. **Installationsskript aufrufen:**
   - Öffnen Sie im Browser:
     ```
     https://ihre-domain.de/api/install.php
     ```
   - Oder:
     ```
     https://ihre-domain.de/stundenzettel/api/install.php
     ```
   - (Je nachdem, wo Sie die Dateien hochgeladen haben)

2. **Installationsprozess:**
   - Das Skript führt automatisch aus:
     - ✅ Datenbankverbindung testen
     - ✅ Datenbank-Tabellen erstellen
     - ✅ Standard-Admin-Account anlegen
     - ✅ System-Checks durchführen
   
3. **Bei Fehlern:**
   - Prüfen Sie die Fehlermeldungen
   - Überprüfen Sie die Datenbank-Konfiguration
   - Siehe Abschnitt [Fehlerbehebung](#fehlerbehebung)

4. **Nach erfolgreicher Installation:**
   - ⚠️ **WICHTIG:** Löschen Sie `install.php` für Sicherheit!
   - Via FTP: `api/install.php` löschen

---

### Schritt 8: Frontend-Dateien hochladen

**Option A: Build aus lokalem Projekt**

1. **Frontend lokal builden:**
   ```bash
   cd frontend
   npm install
   # .env erstellen:
   echo "REACT_APP_BACKEND_URL=https://ihre-domain.de/api" > .env
   npm run build
   ```

2. **Build hochladen:**
   - Laden Sie den Inhalt von `frontend/build/` auf den Server
   - Ziel: `/html/` oder `/html/stundenzettel/`
   - Struktur:
     ```
     /html/
     ├── index.html
     ├── static/
     │   ├── css/
     │   └── js/
     └── manifest.json
     ```

**Option B: Direkt vom Repository**

1. **Frontend-Ordner hochladen:**
   - Laden Sie den `frontend/` Ordner hoch
   - **Aber:** Das wird nicht funktionieren ohne Build!
   - Sie müssen lokal builden (siehe Option A)

---

### Schritt 9: .htaccess konfigurieren

1. **`.htaccess` im Root-Verzeichnis erstellen:**
   
   Erstellen Sie `/html/.htaccess`:

   ```apache
   # PHP-Version setzen
   AddHandler application/x-httpd-php74 .php
   # Oder für PHP 8.0:
   # AddHandler application/x-httpd-php80 .php

   # URL-Rewriting aktivieren
   RewriteEngine On
   RewriteBase /

   # API-Routes weiterleiten
   RewriteRule ^api/(.*)$ api/index.php [QSA,L]

   # Frontend-Routes (React Router)
   RewriteCond %{REQUEST_FILENAME} !-f
   RewriteCond %{REQUEST_FILENAME} !-d
   RewriteRule ^ index.html [L]

   # Sicherheit - Konfigurationsdateien schützen
   <Files "config/database.php">
       Order allow,deny
       Deny from all
   </Files>

   # Installationsskript schützen (nach Installation löschen!)
   <Files "install.php">
       Order allow,deny
       Deny from all
   </Files>

   # CORS-Header (falls nötig)
   Header set Access-Control-Allow-Origin "*"
   Header set Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS"
   Header set Access-Control-Allow-Headers "Content-Type, Authorization"

   # PHP-Einstellungen
   php_value upload_max_filesize 10M
   php_value post_max_size 10M
   php_value memory_limit 256M
   php_value max_execution_time 300

   # Security Headers
   <IfModule mod_headers.c>
       Header set X-Frame-Options "DENY"
       Header set X-Content-Type-Options "nosniff"
       Header set X-XSS-Protection "1; mode=block"
       Header set Referrer-Policy "strict-origin-when-cross-origin"
   </IfModule>
   ```

2. **Falls .htaccess nicht funktioniert:**
   - Überprüfen Sie, ob `mod_rewrite` aktiviert ist
   - Kontaktieren Sie All-inkl Support
   - Alternative: Nutzen Sie Subdomain für API (z.B. `api.ihre-domain.de`)

---

### Schritt 10: SSL/HTTPS einrichten

1. **Let's Encrypt SSL aktivieren:**
   - Im All-inkl Kundenmenü: **"SSL/TLS"** → **"Let's Encrypt SSL"**
   - Domain auswählen
   - **"SSL-Zertifikat erstellen"** klicken
   - Warten Sie einige Minuten (meist automatisch)

2. **HTTPS erzwingen:**
   
   Ergänzen Sie `.htaccess`:

   ```apache
   # HTTPS erzwingen
   RewriteCond %{HTTPS} off
   RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
   ```

3. **Mixed Content verhindern:**
   - Stellen Sie sicher, dass alle URLs HTTPS verwenden
   - Frontend `.env`: `REACT_APP_BACKEND_URL=https://ihre-domain.de/api`

---

### Schritt 11: SMTP konfigurieren

1. **In der Anwendung anmelden:**
   - URL: `https://ihre-domain.de`
   - **E-Mail:** `admin@schmitz-intralogistik.de`
   - **Passwort:** `admin123`
   - ⚠️ **SOFORT Passwort ändern!**

2. **2FA einrichten:**
   - Nach Login wird 2FA-Setup angezeigt
   - QR-Code mit Google Authenticator scannen
   - 6-stellige Code eingeben
   - ✅ 2FA ist obligatorisch!

3. **SMTP konfigurieren:**
   
   Im Admin-Panel: **"Admin"** → **"SMTP Konfiguration"**

   **Option A: All-inkl Mail-Server:**
   ```
   SMTP Server: mail.kasserver.com
   SMTP Port: 587
   SMTP Username: ihre-email@ihre-domain.de
   SMTP Password: ihr-email-passwort
   Admin E-Mail: admin@ihre-domain.de
   ```

   **Option B: Gmail:**
   ```
   SMTP Server: smtp.gmail.com
   SMTP Port: 587
   SMTP Username: ihre-email@gmail.com
   SMTP Password: [App-Passwort, nicht normales Passwort!]
   Admin E-Mail: admin@ihre-domain.de
   ```
   - Für Gmail: App-Passwort in Google Account erstellen (2FA erforderlich)

   **Option C: Outlook/Office 365:**
   ```
   SMTP Server: smtp-mail.outlook.com
   SMTP Port: 587
   SMTP Username: ihre-email@outlook.com
   SMTP Password: ihr-passwort
   Admin E-Mail: admin@ihre-domain.de
   ```

4. **SMTP testen:**
   - Erstellen Sie einen Test-Stundenzettel
   - PDF per E-Mail versenden
   - Überprüfen Sie, ob E-Mail ankommt

---

## 🎯 Erste Schritte nach Installation

### 1. Sicherheit

- [ ] Admin-Passwort geändert
- [ ] 2FA eingerichtet
- [ ] `install.php` gelöscht
- [ ] `.htaccess` korrekt konfiguriert
- [ ] HTTPS aktiviert
- [ ] Datenbank-Passwort stark

### 2. Benutzerverwaltung

- [ ] Ersten Mitarbeiter anlegen (Admin-Panel)
- [ ] Wochenstunden konfigurieren (Standard: 40h)
- [ ] Rollen vergeben (User, Admin, Buchhaltung)

### 3. Testen

- [ ] Test-Stundenzettel erstellen
- [ ] PDF-Generierung testen
- [ ] E-Mail-Versand testen
- [ ] Mobile Ansicht testen
- [ ] Verschiedene Browser testen

---

## 🔧 Fehlerbehebung

### Problem: "Datenbankverbindung fehlgeschlagen"

**Lösung:**
1. Überprüfen Sie, ob der Datenbankname das **Kürzel enthält**
   - Falsch: `stundenzettel`
   - Richtig: `k123456_stundenzettel`
2. Überprüfen Sie den Hostname
   - Meist: `localhost`
   - Alternative: `127.0.0.1`
3. Überprüfen Sie Benutzername und Passwort
4. Testen Sie die Verbindung in phpMyAdmin
5. Prüfen Sie, ob der Benutzer der Datenbank zugeordnet ist

### Problem: "403 Forbidden" bei API-Aufrufen

**Lösung:**
1. Überprüfen Sie `.htaccess` Datei
2. Stellen Sie sicher, dass `mod_rewrite` aktiviert ist
3. Überprüfen Sie Dateiberechtigungen (755 für Ordner, 644 für Dateien)
4. Kontaktieren Sie All-inkl Support bei Problemen

### Problem: "500 Internal Server Error"

**Lösung:**
1. Aktivieren Sie PHP-Fehleranzeige temporär:
   ```php
   error_reporting(E_ALL);
   ini_set('display_errors', 1);
   ```
2. Prüfen Sie PHP-Logs in All-inkl Kundenmenü
3. Überprüfen Sie PHP-Version (7.4+ erforderlich)
4. Prüfen Sie, ob alle Extensions aktiviert sind

### Problem: "CORS-Fehler"

**Lösung:**
1. Überprüfen Sie Frontend `.env`:
   ```
   REACT_APP_BACKEND_URL=https://ihre-domain.de/api
   ```
2. Stellen Sie sicher, dass Backend CORS-Header sendet
3. Überprüfen Sie `.htaccess` CORS-Header

### Problem: "Composer nicht gefunden"

**Lösung:**
- All-inkl bietet meist keinen CLI-Zugang
- Alle PHP-Abhängigkeiten müssen bereits im Code enthalten sein
- Falls Composer benötigt wird: Lokal ausführen und `vendor/` hochladen

### Problem: "Upload-Limit überschritten"

**Lösung:**
1. Erhöhen Sie in `.htaccess`:
   ```apache
   php_value upload_max_filesize 10M
   php_value post_max_size 10M
   ```
2. Falls das nicht funktioniert: All-inkl Support kontaktieren

### Problem: "PDF-Generierung funktioniert nicht"

**Lösung:**
1. Überprüfen Sie, ob TCPDF korrekt hochgeladen wurde
2. Prüfen Sie Schreibrechte für temporäre Dateien
3. Überprüfen Sie PHP `memory_limit` (mindestens 128M)

---

## 📊 All-inkl spezifische Hinweise

### Dateiberechtigungen

- **Ordner:** 755 (drwxr-xr-x)
- **Dateien:** 644 (-rw-r--r--)
- **Ausführbare Scripts:** 755
- **Konfigurationsdateien:** 600 (falls möglich)

### Datenbank-Hostname

- **Meist:** `localhost`
- **Alternative:** `127.0.0.1`
- **Nicht:** Externe IP-Adresse
- **In seltenen Fällen:** `mysql.kasserver.com` (siehe All-inkl Dokumentation)

### PHP Memory Limit

- Standard bei All-inkl: Meist 128M
- Kann über `.htaccess` erhöht werden:
  ```apache
  php_value memory_limit 256M
  ```

### Cronjobs

- All-inkl bietet Cronjob-Verwaltung im Kundenmenü
- Für regelmäßige Backups können Sie Cronjobs einrichten
- Beispiel: Tägliches Backup um 2 Uhr:
  ```
  0 2 * * * /pfad/zum/backup-script.sh
  ```

### Backups

**MongoDB/MySQL Backup:**
- Im All-inkl Kundenmenü: **"Backups"**
- Regelmäßige automatische Backups verfügbar
- Oder: phpMyAdmin → Export

**Dateien Backup:**
- Via FTP: Alle Dateien lokal herunterladen
- Oder: All-inkl Backup-Funktion nutzen

---

## 🔄 Updates installieren

### 1. Backup erstellen

- Datenbank-Export via phpMyAdmin
- Dateien via FTP herunterladen

### 2. Updates hochladen

```bash
# Lokal:
git pull origin main

# Oder: Neue Dateien vom Repository herunterladen
```

### 3. Dateien ersetzen

- Neue Dateien via FTP hochladen
- **WICHTIG:** `.env` und `config/database.php` nicht überschreiben!

### 4. Datenbank-Migrationen

- Falls Datenbank-Schema geändert wurde:
  - Installationsskript erneut ausführen (prüft automatisch)
  - Oder: Migration-Skripte manuell ausführen

---

## 📞 Support & Kontakt

### All-inkl Support

- **Support-Hotline:** In Ihrem Kundenmenü
- **Support-Ticket:** Via Kundenmenü erstellen
- **Dokumentation:** https://all-inkl.com/wichtig/faq/

### Standard-Anmeldedaten

- **E-Mail:** `admin@schmitz-intralogistik.de`
- **Passwort:** `admin123`
- ⚠️ **SOFORT nach Installation ändern!**

### Nützliche URLs nach Installation

- **Frontend:** `https://ihre-domain.de`
- **API:** `https://ihre-domain.de/api`
- **phpMyAdmin:** Via All-inkl Kundenmenü
- **FTP-Zugang:** Via FTP-Client

---

## ✅ Installations-Checkliste für All-inkl

- [ ] Datenbank erstellt (mit Kürzel im Namen!)
- [ ] Datenbankbenutzer erstellt und zugeordnet
- [ ] PHP-Version 7.4+ aktiviert
- [ ] PHP-Extensions aktiviert
- [ ] FTP-Verbindung erfolgreich getestet
- [ ] Backend-Dateien hochgeladen
- [ ] `config/database.php` konfiguriert (MIT Kürzel!)
- [ ] Installation ausgeführt (`install.php`)
- [ ] `install.php` gelöscht (Sicherheit!)
- [ ] Frontend gebaut und hochgeladen
- [ ] `.htaccess` erstellt und konfiguriert
- [ ] SSL/HTTPS aktiviert
- [ ] Erste Anmeldung erfolgreich
- [ ] 2FA eingerichtet
- [ ] Admin-Passwort geändert
- [ ] SMTP konfiguriert
- [ ] Test-Stundenzettel erstellt
- [ ] E-Mail-Versand getestet
- [ ] Mobile Ansicht getestet

---

**Installation auf All-inkl.com abgeschlossen! 🎉**

Bei Fragen oder Problemen siehe Fehlerbehebung oder kontaktieren Sie den All-inkl Support.

