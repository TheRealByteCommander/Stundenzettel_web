# Datenbank-Konfiguration - Schmitz Intralogistik Zeiterfassung

## 🗄️ Datenbankverbindung konfigurieren

Die Datenbankverbindung wird in der Datei `api/config/database.php` konfiguriert.

### Standard-Konfiguration bearbeiten

Öffnen Sie die Datei `api/config/database.php` und passen Sie folgende Werte an:

```php
<?php
class Database {
    // 🔧 DIESE WERTE ANPASSEN:
    private $host = 'localhost';              // MySQL Server-Adresse
    private $database = 'schmitz_timesheet';  // Name der Datenbank
    private $username = 'root';               // MySQL Benutzername
    private $password = '';                   // MySQL Passwort
    
    // ... Rest der Klasse NICHT ändern
}
?>
```

## 📋 Konfigurations-Beispiele

### Lokaler Entwicklungsserver (XAMPP/WAMP/MAMP)
```php
private $host = 'localhost';
private $database = 'schmitz_timesheet';
private $username = 'root';
private $password = '';  // Oft leer bei lokalen Servern
```

### Shared Hosting (Standard Webhosting)
```php
private $host = 'localhost';           // Oft 'localhost'
private $database = 'ihr_account_schmitz_timesheet';  // Oft mit Prefix
private $username = 'ihr_account_user';               // Vom Hoster bereitgestellt
private $password = 'ihr_sicheres_passwort';          // Vom Hoster bereitgestellt
```

### VPS/Root Server
```php
private $host = 'localhost';           // oder IP-Adresse
private $database = 'schmitz_timesheet';
private $username = 'schmitz_user';    // Separater DB-User empfohlen
private $password = 'ein_starkes_passwort123!';
```

### Remote MySQL Server
```php
private $host = 'mysql.ihre-domain.de';  // Remote Server-Adresse
private $database = 'schmitz_timesheet';
private $username = 'remote_user';
private $password = 'remote_passwort';
```

### Cloud-Datenbank (AWS RDS, Google Cloud SQL)
```php
private $host = 'instance.region.rds.amazonaws.com';  // AWS RDS Endpoint
private $database = 'schmitz_timesheet';
private $username = 'admin';
private $password = 'cloud_db_passwort';
```

## 🔐 Datenbank-Benutzer erstellen (Empfohlen)

Für bessere Sicherheit sollten Sie einen separaten Datenbankbenutzer erstellen:

### MySQL-Kommandos
```sql
-- 1. Datenbank erstellen
CREATE DATABASE schmitz_timesheet CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. Benutzer erstellen
CREATE USER 'schmitz_user'@'localhost' IDENTIFIED BY 'ihr_sicheres_passwort';

-- 3. Berechtigung für die Datenbank vergeben
GRANT ALL PRIVILEGES ON schmitz_timesheet.* TO 'schmitz_user'@'localhost';

-- 4. Berechtigung aktualisieren
FLUSH PRIVILEGES;
```

### Entsprechende Konfiguration
```php
private $host = 'localhost';
private $database = 'schmitz_timesheet';
private $username = 'schmitz_user';
private $password = 'ihr_sicheres_passwort';
```

## 🌐 Hosting-Provider Spezifika

### 1&1 IONOS
```php
private $host = 'dbXXXXX.db.1and1.com';        // Von IONOS bereitgestellt
private $database = 'dbXXXXX';                 // Datenbankname
private $username = 'dboXXXXX';                // DB-Benutzername
private $password = 'ihr_db_passwort';         // Selbst gesetzt
```

### Strato
```php
private $host = 'rdbms.strato.de';
private $database = 'DB123456';
private $username = 'U123456';
private $password = 'ihr_db_passwort';
```

### ALL-INKL.COM
```php
private $host = 'mysql.ihr-account.com';
private $database = 'ihr_account_db1';
private $username = 'ihr_account';
private $password = 'ihr_db_passwort';
```

### Host Europe
```php
private $host = 'mysql.ihr-domain.de';
private $database = 'db123456_1';
private $username = 'db123456';
private $password = 'ihr_db_passwort';
```

## 🔍 Verbindung testen

### Automatischer Test
Nach der Konfiguration öffnen Sie: `https://ihre-domain.de/api/install.php`

Der Installer testet automatisch die Datenbankverbindung.

### Manueller Test
Erstellen Sie eine Testdatei `db_test.php`:

```php
<?php
require_once 'api/config/database.php';

try {
    $database = new Database();
    $db = $database->getConnection();
    echo "✅ Datenbankverbindung erfolgreich!";
} catch (Exception $e) {
    echo "❌ Fehler: " . $e->getMessage();
}
?>
```

## ⚠️ Häufige Probleme

### Problem: "Access denied for user"
**Ursache**: Falscher Benutzername oder Passwort
**Lösung**: 
- Daten beim Hosting-Provider überprüfen
- Passwort zurücksetzen
- Benutzerberechtigungen kontrollieren

### Problem: "Unknown database"
**Ursache**: Datenbank existiert nicht
**Lösung**:
- Datenbank im Hosting-Panel erstellen
- Datenbankname in der Konfiguration überprüfen

### Problem: "Can't connect to MySQL server"
**Ursache**: Falscher Host oder Server nicht erreichbar
**Lösung**:
- Host-Adresse beim Provider erfragen
- Firewall-Einstellungen überprüfen
- Port-Nummer ergänzen (falls nicht 3306)

### Problem: "Connection timed out"
**Ursache**: Langsame oder überlastete Verbindung
**Lösung**:
- Timeout in der Konfiguration erhöhen
- Hosting-Provider kontaktieren

## 🔧 Erweiterte Konfiguration

### Custom Port
Falls MySQL auf einem anderen Port läuft:
```php
private $host = 'localhost:3307';  // Port 3307 statt 3306
```

### SSL-Verbindung
Für verschlüsselte Verbindungen:
```php
public function getConnection() {
    $this->conn = null;
    try {
        $options = [
            PDO::MYSQL_ATTR_SSL_CA => '/path/to/ca.pem',
            PDO::MYSQL_ATTR_SSL_VERIFY_SERVER_CERT => false,
        ];
        
        $this->conn = new PDO(
            "mysql:host=" . $this->host . ";dbname=" . $this->database . ";charset=utf8",
            $this->username,
            $this->password,
            $options
        );
        // ... Rest unverändert
    }
    // ... Rest unverändert
}
```

### Connection Pooling
Für bessere Performance:
```php
public function getConnection() {
    $this->conn = null;
    try {
        $options = [
            PDO::ATTR_PERSISTENT => true,          // Persistente Verbindungen
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::MYSQL_ATTR_INIT_COMMAND => "SET NAMES utf8"
        ];
        
        $this->conn = new PDO(
            "mysql:host=" . $this->host . ";dbname=" . $this->database . ";charset=utf8",
            $this->username,
            $this->password,
            $options
        );
    }
    // ... Rest unverändert
}
```

## 💾 Backup-Konfiguration

### Automatisches Backup
Ergänzen Sie in `database.php`:
```php
public function createBackup($backupPath = 'backups/') {
    $filename = $backupPath . 'backup_' . date('Y-m-d_H-i-s') . '.sql';
    $command = "mysqldump -h{$this->host} -u{$this->username} -p{$this->password} {$this->database} > {$filename}";
    exec($command, $output, $return_var);
    
    if ($return_var === 0) {
        return $filename;
    } else {
        throw new Exception("Backup failed");
    }
}
```

## 📊 Performance-Optimierung

### Connection Limits
Überwachen Sie die Anzahl der Datenbankverbindungen:
```sql
SHOW STATUS LIKE 'Connections';
SHOW STATUS LIKE 'Max_used_connections';
SHOW VARIABLES LIKE 'max_connections';
```

### Index-Optimierung
Nach der Installation können Sie Indizes hinzufügen:
```sql
-- Index für bessere Performance bei Timesheet-Abfragen
CREATE INDEX idx_user_date ON timesheets(user_id, week_start);
CREATE INDEX idx_status ON timesheets(status);
CREATE INDEX idx_created ON timesheets(created_at);
```

## 🆘 Support-Checkliste

Bei Datenbankproblemen prüfen Sie:

- [ ] Sind Host, Datenbankname, Benutzername und Passwort korrekt?
- [ ] Existiert die Datenbank?
- [ ] Hat der Benutzer die erforderlichen Rechte?
- [ ] Ist der MySQL-Server erreichbar?
- [ ] Sind alle PHP-Erweiterungen installiert (pdo, pdo_mysql)?
- [ ] Funktioniert die Verbindung mit einem MySQL-Client?
- [ ] Sind Firewall-Regeln korrekt konfiguriert?

## 📞 Hosting-Provider kontaktieren

Falls weiterhin Probleme auftreten, kontaktieren Sie Ihren Hosting-Provider mit folgenden Informationen:

1. **Fehlercode**: Genaue Fehlermeldung
2. **PHP-Version**: `php -v` oder in phpinfo()
3. **MySQL-Version**: `SELECT VERSION();`
4. **Konfiguration**: Ihre aktuellen Datenbankeinstellungen (ohne Passwort!)
5. **Log-Dateien**: PHP- und MySQL-Error-Logs

---

**Nach erfolgreicher Konfiguration können Sie mit der Installation fortfahren:**
➡️ `https://ihre-domain.de/api/install.php`