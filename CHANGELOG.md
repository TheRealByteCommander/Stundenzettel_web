# Changelog

Alle wichtigen Änderungen in diesem Projekt werden in dieser Datei dokumentiert.

## [Unreleased]

### Hinzugefügt
- **Stundenzettel-Verifikation**: 
  - Upload unterschriebener Stundenzettel (vom Kunden unterzeichnet)
  - Automatische Verifikation der Unterschrift durch Dokumenten-Agent (PDF-Text-Analyse)
  - Stunden werden nur aus verifizierten, unterschriebenen und freigegebenen Stundenzetteln gezählt
  - Freigabe-Button nur aktiv, wenn unterschriebene PDF vorhanden oder ausschließlich Abwesenheitstage
  - Visuelle Anzeige des Verifikationsstatus (Badge: "Unterschrift verifiziert" / "Unterschrift hochgeladen")
- **Reisekosten-App**: Vollständige Implementierung der Reisekostenabrechnung
  - Automatische Befüllung aus genehmigten, **verifizierten** Stundenzetteln (Ort, Tage, Fahrzeit, Kunde)
  - Monatsauswahl (aktueller Monat + max 2 Monate zurück)
  - PDF-Beleg-Upload mit lokaler Speicherung (nicht auf Webserver)
  - Status-Management: Entwurf → Abgeschlossen → In Prüfung → Genehmigt
  - Chat-System für Rückfragen zwischen User und Agenten
  - Lösch- und Bearbeitungsfunktionen für Entwürfe
  - **Validierung vor Einreichen**: System prüft, ob für alle Tage verifizierte Stundenzettel vorhanden sind
  - **Übersicht abgedeckte/fehlende Tage**: UI zeigt welche Tage abgedeckt sind und welche fehlen
  - **Reisekosten nur für verifizierte Stundenzettel**: Fehlende Tage werden nicht in Reisekosten einbezogen
- **Ankündigungen-System**: Admin kann Nachrichten/Ankündigungen mit Bildern erstellen
  - Anzeige auf der App-Auswahlseite
  - Bild-Upload (Base64-kodiert)
  - Aktiv/Inaktiv-Status
  - CRUD-Operationen für Admins
- **Ollama LLM Integration**: Vollständig implementiert für automatische Prüfung von Reisekostenabrechnungen
  - Dokumenten-Agent: Automatische Verifikation unterschriebener Stundenzettel
  - Automatische Agenten-Antworten im Chat-System

### Geändert
- **Backend**: 
  - `WeeklyTimesheet` Modell erweitert um `signed_pdf_verified` und `signed_pdf_verification_notes`
  - Upload-Endpunkt führt automatische Verifikation durch Dokumenten-Agent aus
  - Statistiken berücksichtigen nur verifizierte, unterschriebene Stundenzettel
  - Reisekosten-Initialisierung verwendet nur verifizierte Stundenzettel
  - Reisekosten-Einreichung validiert Vorhandensein verifizierter Stundenzettel für alle Tage
- **Frontend**: 
  - Freigabe-Button logik erweitert: Prüft auf unterschriebene PDF oder nur Abwesenheitstage
  - Reisekosten-UI zeigt Übersicht abgedeckte/fehlende Tage
  - Button zum Einreichen deaktiviert, wenn Tage fehlen (mit Hinweis)
  - Verifikationsstatus-Badge in Stundenzettel-Liste

### In Entwicklung
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

