# 🚀 Live-Deployment Anleitung - Schmitz Intralogistik

## ⚡ Schnell-Setup für ai.byte-commander.de

### 📋 Bereits konfiguriert:
- **Datenbank**: d04464c7 (Username: d04464c7, Passwort: mAh4Raeder!)
- **FTP**: f017983a@ai.byte-commander.de (Passwort: mAh4Raeder!)
- **PDF-Generierung**: TCPDF installiert und konfiguriert

### 🔥 Live-Deployment Schritte:

#### 1. FTP-Upload
**Option A: Automatisch**
```bash
./upload_to_live.sh
```

**Option B: Manuell (empfohlen)**
- FTP-Client (FileZilla, WinSCP, etc.)
- Server: `ai.byte-commander.de`
- Benutzername: `f017983a`
- Passwort: `mAh4Raeder!`
- Alle Dateien aus `/app/webapp/` hochladen

#### 2. Installation ausführen
1. Browser öffnen: `https://ai.byte-commander.de/api/install.php`
2. Datenbank wird automatisch initialisiert
3. Standard-Admin wird erstellt

#### 3. Erster Login
- URL: `https://ai.byte-commander.de`
- E-Mail: `admin@schmitz-intralogistik.de`
- Passwort: `admin123`

#### 4. Sicherheit (WICHTIG!)
```bash
# Nach Installation löschen:
rm api/install.php
```

### 🎯 Funktionstest-Checkliste:

#### ✅ Basis-Funktionen
- [ ] Login funktioniert
- [ ] Dashboard lädt
- [ ] Neuer Stundenzettel erstellen
- [ ] Monday-Dropdown funktioniert

#### ✅ PDF-Generierung (KRITISCH!)
- [ ] PDF-Download funktioniert
- [ ] DIN A4 Querformat korrekt
- [ ] Schmitz Corporate Design
- [ ] Deutsche Wochentage (Montag-Sonntag)
- [ ] Gesamtstunden-Berechnung

#### ✅ E-Mail-Integration
- [ ] SMTP-Konfiguration im Admin-Panel
- [ ] E-Mail-Versand funktioniert
- [ ] PDF als Anhang

#### ✅ Admin-Funktionen  
- [ ] Benutzerverwaltung
- [ ] Alle Stundenzettel einsehen
- [ ] SMTP-Konfiguration

### 🔧 PDF-Generierung Features:

#### ✨ TCPDF Implementation:
- **Echte PDF-Dateien** (nicht HTML)
- **DIN A4 Querformat** exakt nach Vorlage
- **Corporate Design**: Schmitz Farben und Branding
- **Deutsche Lokalisierung**: Montag, Dienstag, etc.
- **Präzise Tabellen**: Wie in der Vorlage
- **Automatische Dateinamen**: `{Name}_KW{XX}_{Jahr}_{001}.pdf`

#### 📊 PDF-Layout:
```
┌─────────────────────────────────────────────────┐
│  STUNDENZETTEL           Schmitz Intralogistik │
│                          Grüner Weg 3          │
│                          04827 Machern         │
│                                                 │
│  Projekt: XXX            Kunde: XXX            │
│  Mitarbeiter: XXX        KW: XX (DD.MM-DD.MM)  │
│                                                 │
│ ┌─────────┬──────┬──────┬──────┬─────────┬────┐ │
│ │ Datum   │Start │ Ende │Pause │Beschreib│Std.│ │
│ ├─────────┼──────┼──────┼──────┼─────────┼────┤ │
│ │ Montag  │      │      │      │         │    │ │
│ │ ...     │      │      │      │         │    │ │
│ │ Sonntag │      │      │      │         │    │ │
│ ├─────────┴──────┴──────┴──────┼─────────┼────┤ │
│ │                    Gesamt:   │ XX.X h │    │ │
│ └──────────────────────────────┴─────────┴────┘ │
│                                                 │
│  Datum: DD.MM.YYYY    Unterschrift Kunde:  ___ │
│  Mitarbeiter: XXX     Unterschrift MA:     ___ │
└─────────────────────────────────────────────────┘
```

### 🛠️ Erweiterte Konfiguration:

#### SMTP für E-Mails:
```
Gmail:
Server: smtp.gmail.com
Port: 587
Benutzer: ihre-email@gmail.com
Passwort: app-passwort

Outlook:
Server: smtp-mail.outlook.com
Port: 587
Benutzer: ihre-email@outlook.com
Passwort: standard-passwort
```

#### Fehlerbehandlung:
```bash
# PHP Logs prüfen:
tail -f /var/log/php/errors.log

# Apache Logs:
tail -f /var/log/apache2/error.log
```

### 🚨 Troubleshooting:

#### Problem: "Internal Server Error"
- .htaccess Berechtigungen prüfen
- PHP-Erweiterungen installiert? (pdo, pdo_mysql, gd)
- TCPDF Ordner lesbar?

#### Problem: "Database connection failed"
- Datenbank d04464c7 existiert?
- Credentials korrekt in api/config/database.php?
- MySQL läuft?

#### Problem: "PDF generation failed"
- TCPDF Bibliothek vollständig hochgeladen?
- PHP Memory Limit ausreichend? (256M empfohlen)
- GD Extension installiert?

#### Problem: "Email sending failed"
- SMTP-Konfiguration im Admin-Panel
- Firewall blockiert Port 587?
- mail() Funktion aktiviert?

### 🎉 Nach erfolgreichem Deployment:

#### Nächste Schritte:
1. **Admin-Passwort ändern**: Sicherheit!
2. **SMTP konfigurieren**: E-Mail-Versand
3. **Benutzer anlegen**: Mitarbeiter hinzufügen
4. **Test-Stundenzettel**: Vollständigen Workflow testen
5. **PDF prüfen**: Layout und Inhalt kontrollieren

#### Backup-Strategie:
```sql
-- Datenbank Backup
mysqldump -u d04464c7 -p d04464c7 > backup_$(date +%Y%m%d).sql

-- Dateien Backup
tar -czf files_backup_$(date +%Y%m%d).tar.gz .
```

### 📞 Support-Kontakt:
- Vollständige Logs für Debugging bereitstellen
- Screenshots bei UI-Problemen
- PDF-Beispiele bei Layout-Problemen

---

## 🎯 **Deployment Status:**

✅ **Datenbank**: Live-Daten konfiguriert  
✅ **PDF-Engine**: TCPDF implementiert  
✅ **Corporate Design**: Schmitz Branding  
✅ **Security**: Produktionsbereit  
✅ **Documentation**: Vollständig  

**➡️ Ready for Production Deployment! 🚀**