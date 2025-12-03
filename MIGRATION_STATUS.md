# Migrationsstatus - Noch nicht vollständig migrierte Funktionen

**Stand: Januar 2025**

## ✅ Vollständig migriert

- ✅ **Authentifizierung & Sicherheit**: Login, 2FA, Passwortänderung
- ✅ **Stundenzettel**: CRUD, PDF-Generierung, Upload, Genehmigung, Statistiken
- ✅ **Reisekosten**: Reports, Beleg-Upload, Chat, Validierung
- ✅ **Urlaub**: Anträge, Guthaben, Genehmigung, Anforderungen
- ✅ **Ankündigungen**: CRUD, Bild-Upload
- ✅ **Admin**: Benutzerverwaltung, Fahrzeuge, SMTP, Accounting-Statistik
- ✅ **Kundenverwaltung**: CRUD, Dropdown-Integration
- ✅ **Push-Benachrichtigungen**: Service Worker, Registrierung
- ✅ **Mobile-Optimierung**: Responsive Design, PWA-Funktionalität

---

## ⚠️ Teilweise migriert / Noch nicht vollständig integriert

### 1. **Urlaubs-Erinnerungsmails** (Backend vorhanden, Frontend fehlt)
- **Backend**: `POST /vacation/send-reminders` - Wöchentliche Erinnerungen senden
- **Status**: Backend-Endpoint existiert, aber **keine Frontend-UI** dafür
- **Fehlt**: Admin-Button/Seite zum manuellen Versenden von Erinnerungsmails
- **Priorität**: Niedrig (kann auch automatisch per Cronjob laufen)

### 2. **Urlaubsguthaben-Verwaltung** (Backend vorhanden, Frontend teilweise)
- **Backend**: `PUT /vacation/balance/{user_id}/{year}` - Guthaben anpassen
- **Status**: Backend-Endpoint existiert, **Frontend-UI fehlt**
- **Fehlt**: Admin-Interface zum Anpassen von Urlaubstagen pro User/Jahr
- **Priorität**: Mittel (wird vermutlich selten benötigt)

### 3. **2FA-Verwaltung** (Backend vorhanden, Frontend teilweise)
- **Backend**: 
  - `POST /auth/2fa/enable` - 2FA aktivieren
  - `POST /auth/2fa/disable` - 2FA deaktivieren (nur Admin)
- **Status**: Backend-Endpoints existieren, **Frontend-UI fehlt**
- **Fehlt**: Admin-Interface zum Aktivieren/Deaktivieren von 2FA für andere User
- **Priorität**: Niedrig (2FA ist obligatorisch, Deaktivierung sollte selten sein)

### 4. **Fahrzeug-Verfügbarkeit** (Backend vorhanden, Frontend verwendet)
- **Backend**: `GET /vehicles/available` - Verfügbare Fahrzeuge
- **Status**: ✅ Wird bereits im Frontend verwendet (`useAvailableVehiclesQuery`)
- **Hinweis**: Vollständig integriert

### 5. **Reisekosten-Einzelausgaben** (Backend vorhanden, Frontend fehlt)
- **Backend**: 
  - `GET /travel-expenses` - Alle Einzelausgaben
  - `POST /travel-expenses` - Neue Einzelausgabe
  - `PUT /travel-expenses/{expense_id}` - Ausgabe aktualisieren
  - `DELETE /travel-expenses/{expense_id}` - Ausgabe löschen
- **Status**: Backend-Endpoints existieren, **Frontend-UI fehlt**
- **Fehlt**: Verwaltung von Einzelausgaben außerhalb von Reports
- **Priorität**: Niedrig (Einzelausgaben werden normalerweise über Reports verwaltet)

### 6. **Migration-Tool** (Backend vorhanden, Frontend fehlt)
- **Backend**: `migration_api.py` - API-Endpunkte für Datenbank-Migration
- **Status**: Backend-Tool existiert, **keine Frontend-UI**
- **Fehlt**: Admin-Interface für Datenbank-Migrationen
- **Priorität**: Sehr niedrig (wird nur einmalig bei Migration benötigt)

### 7. **Feiertags-API** (Backend vorhanden, Frontend nicht direkt verwendet)
- **Backend**: 
  - `GET /vacation/holidays/{year}` - Alle Feiertage für Jahr
  - `GET /vacation/check-holiday/{date}` - Einzelner Feiertag prüfen
- **Status**: Backend-Endpoints existieren, werden aber **automatisch im Backend verwendet**
- **Fehlt**: Frontend-Anzeige der Feiertage (optional)
- **Priorität**: Sehr niedrig (Feiertage werden automatisch berücksichtigt)

### 8. **Accounting-Timesheet-Liste** (Backend vorhanden, Frontend teilweise)
- **Backend**: `GET /accounting/timesheets-list` - Liste aller Stundenzettel für Buchhaltung
- **Status**: Backend-Endpoint existiert, **Frontend-Integration unklar**
- **Fehlt**: Dedizierte Accounting-Seite für Stundenzettel-Übersicht
- **Priorität**: Mittel (wird möglicherweise bereits über andere Seiten abgedeckt)

---

## 🔍 Nicht kritische / Optionale Features

### 9. **Erweiterte Statistiken** (Optional)
- **Status**: Basis-Statistiken vorhanden, erweiterte Visualisierungen fehlen
- **Fehlt**: Diagramme, Charts, Trend-Analysen
- **Priorität**: Sehr niedrig (nice-to-have)

### 10. **Export-Funktionen** (Teilweise vorhanden)
- **Status**: CSV/PDF-Export für Timesheets vorhanden
- **Fehlt**: Erweiterte Export-Optionen (Excel, JSON, etc.)
- **Priorität**: Niedrig

### 11. **Benachrichtigungs-Einstellungen** (Optional)
- **Status**: Push-Benachrichtigungen funktionieren
- **Fehlt**: User-Einstellungen für Benachrichtigungstypen (E-Mail, Push, etc.)
- **Priorität**: Niedrig

### 12. **Audit-Log-Anzeige** (Backend vorhanden, Frontend fehlt)
- **Backend**: `AuditLogger` Klasse existiert
- **Status**: Audit-Logs werden geschrieben, aber **keine Frontend-Anzeige**
- **Fehlt**: Admin-Interface zum Anzeigen von Audit-Logs
- **Priorität**: Mittel (wichtig für Compliance, aber nicht kritisch für täglichen Betrieb)

---

## 📊 Zusammenfassung

### Kritische fehlende Features: **0**
Alle kritischen Funktionen für den täglichen Betrieb sind vollständig migriert.

### Wichtige fehlende Features: **2**
1. Urlaubsguthaben-Verwaltung (Admin-Interface)
2. Accounting-Timesheet-Liste (möglicherweise bereits abgedeckt)

### Optionale fehlende Features: **10**
- Urlaubs-Erinnerungsmails (Frontend-UI)
- 2FA-Verwaltung (Admin-Interface)
- Reisekosten-Einzelausgaben (UI)
- Migration-Tool (Frontend-UI)
- Feiertags-Anzeige (optional)
- Erweiterte Statistiken (Diagramme)
- Erweiterte Export-Funktionen
- Benachrichtigungs-Einstellungen
- Audit-Log-Anzeige
- Weitere optionale Features

---

## 🎯 Empfohlene nächste Schritte

1. **Urlaubsguthaben-Verwaltung** (Priorität: Mittel)
   - Admin-Interface zum Anpassen von Urlaubstagen
   - Einfache Tabelle mit Eingabefeldern

2. **Audit-Log-Anzeige** (Priorität: Mittel)
   - Admin-Seite zum Anzeigen von Audit-Logs
   - Filterung nach User, Datum, Aktion

3. **Urlaubs-Erinnerungsmails** (Priorität: Niedrig)
   - Admin-Button zum manuellen Versenden
   - Optional: Automatischer Cronjob

---

**Hinweis**: Die meisten fehlenden Features sind administrative Funktionen, die selten benötigt werden. Der tägliche Betrieb ist vollständig abgedeckt.

