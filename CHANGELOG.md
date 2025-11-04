# Changelog

Alle wichtigen Änderungen in diesem Projekt werden in dieser Datei dokumentiert.

## [Unreleased]

### Hinzugefügt
- **Urlaubsplaner**: Vollständige Implementierung
  - Urlaubsanträge stellen (Start-/Enddatum, Notizen)
  - Automatische Werktage-Berechnung (Mo-Fr) **mit Ausschluss von Feiertagen**
  - **Feiertags-Integration**: 
    - Deutsche Feiertage (bundesweit) und sächsische Feiertage werden automatisch erkannt
    - Feiertage werden **nicht als Urlaubstage gezählt**
    - Feiertage werden automatisch als "Feiertag" in Stundenzettel eingetragen
    - Feiertage sind programmweit verfügbar und werden automatisch genutzt
    - API-Endpunkte: `/vacation/holidays/{year}` und `/vacation/check-holiday/{date}`
  - Genehmigung/Ablehnung durch Admin/Buchhaltung
  - Urlaubstage-Verwaltung: Admin kann verfügbare Tage pro Mitarbeiter eintragen
  - Automatischer Eintrag genehmigter Urlaubstage in Stundenzettel
  - Validierung: Mindestens 10 Tage am Stück (ohne Feiertage), 20 gesamt (ohne Feiertage), Deadline 01.02.
  - Wöchentliche Erinnerungsmails bei fehlenden Mindestanforderungen
  - Genehmigte Urlaubstage sind nicht mehr änderbar (User)
  - Admin kann genehmigte Urlaubsanträge löschen (aktualisiert Guthaben)
  - UI: Urlaubsplaner-Tab mit Jahr-Auswahl, Guthaben-Anzeige, Validierungshinweisen
- **Stundenzettel-Verifikation und automatische Genehmigung**: 
  - Upload unterschriebener Stundenzettel (vom Kunden unterzeichnet, vom User hochgeladen)
  - **Automatische Verifikation der Unterschrift durch Dokumenten-Agent** (PDF-Text-Analyse)
  - **Automatische Genehmigung**: Wenn Agent Unterschrift verifiziert, wird automatisch als "approved" markiert und Arbeitszeit gutgeschrieben
  - **Buchhaltung genehmigt nur in Ausnahmefällen**: Wenn Agent Unterschrift nicht verifizieren konnte oder nur Abwesenheitstage (Urlaub/Krankheit/Feiertag)
  - Stunden werden nur aus verifizierten, unterschriebenen und genehmigten Stundenzetteln gezählt
  - Freigabe-Button nur aktiv, wenn unterschriebene PDF vorhanden oder ausschließlich Abwesenheitstage
  - Visuelle Anzeige des Verifikationsstatus (Badge: "Unterschrift verifiziert" / "Unterschrift hochgeladen")
  - E-Mail-Benachrichtigung an Buchhaltung: Unterscheidet zwischen automatisch genehmigt und manuelle Prüfung erforderlich
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
  - **Automatische Genehmigung**: Wenn `signed_pdf_verified=True`, wird Status automatisch auf "approved" gesetzt
  - **Genehmigungs-Endpunkt**: Buchhaltung kann nur noch in Ausnahmefällen genehmigen (wenn `signed_pdf_verified=False` oder nur Abwesenheitstage)
  - **E-Mail-Benachrichtigung**: Unterscheidet zwischen automatisch genehmigt und manuelle Prüfung erforderlich
  - Statistiken berücksichtigen nur verifizierte, unterschriebene und genehmigte Stundenzettel
  - Reisekosten-Initialisierung verwendet nur verifizierte Stundenzettel
  - Reisekosten-Einreichung validiert Vorhandensein verifizierter Stundenzettel für alle Tage
  - **Feiertags-Integration**: 
    - `count_working_days()` Funktion erweitert: Feiertage werden automatisch ausgeschlossen
    - `add_vacation_entries_to_timesheet()` erweitert: Feiertage werden automatisch als "feiertag" eingetragen
    - Neue Funktionen: `get_german_holidays()`, `is_holiday()` für programmweite Nutzung
    - `holidays`-Bibliothek zu `requirements.txt` hinzugefügt
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

