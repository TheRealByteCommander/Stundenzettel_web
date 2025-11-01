# Changelog

Alle wichtigen Änderungen in diesem Projekt werden in dieser Datei dokumentiert.

## [Unreleased]

### Hinzugefügt
- **Reisekosten-App**: Vollständige Implementierung der Reisekostenabrechnung
  - Automatische Befüllung aus genehmigten Stundenzetteln (Ort, Tage, Fahrzeit, Kunde)
  - Monatsauswahl (aktueller Monat + max 2 Monate zurück)
  - PDF-Beleg-Upload mit lokaler Speicherung (nicht auf Webserver)
  - Status-Management: Entwurf → Abgeschlossen → In Prüfung → Genehmigt
  - Chat-System für Rückfragen zwischen User und Agenten
  - Lösch- und Bearbeitungsfunktionen für Entwürfe
- **Ankündigungen-System**: Admin kann Nachrichten/Ankündigungen mit Bildern erstellen
  - Anzeige auf der App-Auswahlseite
  - Bild-Upload (Base64-kodiert)
  - Aktiv/Inaktiv-Status
  - CRUD-Operationen für Admins

### In Entwicklung
- Ollama LLM Integration für automatische Prüfung von Reisekostenabrechnungen
- Automatische Agenten-Antworten im Chat-System
- Benachrichtigungen für Buchhaltung bei fertigen Abrechnungen

## [Vorherige Versionen]

### Implementiert
- Obligatorische 2FA (Google Authenticator)
- Rollen-System (User, Admin, Buchhaltung)
- Stundenzettel-Genehmigung durch Buchhaltung
- Urlaub/Krankheit/Feiertag-Tracking
- Fahrzeit-Erfassung mit optionaler Weiterberechnung
- Wochenstunden-Konfiguration pro Mitarbeiter
- Automatische Gutschrift von 8h pro Abwesenheitstag (bei 40h-Vertrag)
- PDF-Generierung für Stundenzettel
- E-Mail-Versand mit PDF-Anhang
- Monatsstatistiken und Rang-System
- App-Auswahlseite nach Login
- Responsive Web-Interface

