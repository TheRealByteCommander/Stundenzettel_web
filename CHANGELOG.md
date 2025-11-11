# Changelog

Alle wichtigen Änderungen in diesem Projekt werden in dieser Datei dokumentiert.

## [Unreleased]

### Geändert
- **Daten aktualisiert**: Alle Dokumente auf Stand 2025 aktualisiert (BENUTZERANLEITUNG.md, SICHERHEIT.md, CYBER_SECURITY.md, README.md)
- **Fahrzeit-Regelung präzisiert**:
  - Nur die **Anreise zum Arbeitsort** wird als Arbeitszeit gewertet
  - Die **tägliche Fahrt Hotel-Kunde** ist **KEINE Arbeitszeit** und sollte nicht als Fahrzeit erfasst werden
  - Frontend: Hinweis bei Fahrzeit-Eingabe hinzugefügt
  - Backend: Kommentare und PDF-Beschriftung aktualisiert ("Fahrzeit Anreise")
  - Dokumentation: Regelung in BENUTZERANLEITUNG.md und README.md klarstellt

### Hinzugefügt
- **Frontend (Neuaufbau)**:
  - Reisekosten-Übersicht mit Monatsinitialisierung und Draft-Detailansicht
  - API-Clients & Hooks für Reisekostenberichte, Beleg-Uploads und Chat-Vorbereitung
- **Timesheets**
  - Wochen- und tageweise Fahrzeugzuordnung bei der Stundenzettel-Erfassung
  - Fahrzeuganzeige in Listen-, Detail- und Buchhaltungsansichten
- **Administration**
  - Fahrzeugverwaltung (Pool-/Mitarbeiterfahrzeuge, Kennzeichenpflege, Zuordnung)
- **Fremdwährungs-Nachweis für Reisekosten-Belege**:
  - Automatische Erkennung von Fremdwährungen (nicht EUR)
  - Erforderlicher Nachweis über tatsächlichen Euro-Betrag (z.B. Kontoauszug)
  - Upload-Funktion für Fremdwährungs-Nachweis
  - Frontend: Gelbe Warnung und Upload-Button bei Fremdwährung
  - Automatische Validierung und Anzeige des Nachweis-Status
  - GoBD-konform: Nachweis wird verschlüsselt gespeichert

### Geändert
- **Reisekosten-App: Vereinfachte Bedienung und automatische Datenextraktion**
  - User lädt nur PDF-Belege hoch - alle Daten werden automatisch extrahiert
  - Automatische Extraktion von Betrag, Datum, Typ, Währung aus PDFs
  - Automatische Zuordnung zu Reiseeinträgen basierend auf Datum
  - **Logik- und Machbarkeitsprüfung**:
    - Überlappende Hotelrechnungen werden automatisch erkannt
    - Datum-Abgleich mit Arbeitsstunden aus Stundenzetteln
    - Zeitliche Konsistenz-Prüfung (z.B. Übernachtung ohne Anreise)
    - Orts-Konsistenz-Prüfung
    - Betrags-Plausibilitäts-Prüfung
  - Chat-Agent wird automatisch bei Problemen aktiviert
  - Frontend: Anzeige extrahierter Daten und Probleme direkt bei jedem Beleg
  - Frontend: Reiseeinträge sind nur noch Anzeige (keine Bearbeitung mehr)
- **Strukturierte Ordner-Speicherung für PDF-Dateien:**
  - Reisekosten-Belege werden in eindeutigen Ordnern gespeichert: `User_Name_Monat_ReportID/`
  - Unterschriebene Stundenzettel werden in eindeutigen Ordnern gespeichert: `User_Name_Woche_TimesheetID/`
  - Alle Belege einer Reisekosten-Abrechnung sind in einem separaten Ordner
  - Beim Löschen einer Abrechnung wird der gesamte Ordner gelöscht
  - Ordner-Struktur: `LOCAL_RECEIPTS_PATH/reisekosten/` und `LOCAL_RECEIPTS_PATH/stundenzettel/`

### Geändert
- **Backend:**
  - `upload_receipt`: 
    - Automatische Dokumentenanalyse beim Upload
    - Automatische Zuordnung zu Reiseeinträgen
    - Logik-Prüfung (überlappende Hotelrechnungen, Datum-Abgleich)
    - Automatische Chat-Agent-Benachrichtigung bei Problemen
  - `DocumentAgent`: Erweitert um Logik-Prüfung (überlappende Rechnungen, Datum-Abgleich mit Arbeitsstunden)
  - `AccountingAgent`: Erweitert um Machbarkeitsprüfung (überlappende Hotelrechnungen, Datum-Konsistenz, zeitliche Machbarkeit)
  - `upload_signed_timesheet`: Erstellt jetzt Ordner pro Stundenzettel
  - `delete_expense_report`: Löscht jetzt den gesamten Ordner der Abrechnung
  - Ordner-Namen: `User_Name_Monat_ReportID` für Reisekosten, `User_Name_Woche_TimesheetID` für Stundenzettel
- **Frontend:**
  - Reisekosten-UI vereinfacht: Nur Upload, keine manuellen Eingabefelder
  - Reiseeinträge: Nur Anzeige (keine Bearbeitung mehr)
  - Belege: Anzeige extrahierter Daten (Betrag, Datum, Typ) und Probleme
  - Automatische Aktualisierung nach Upload

---

## [Frühere Versionen]

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
  - **Validierung und gesetzliche Anforderungen**: 
    - **Gesetzlich (BUrlG §7)**: **Mindestens 2 Wochen am Stück** (10 Werktage, Mo-Fr ohne Feiertage) - gesetzlicher Erholungsurlaub
    - **Betrieblich**: **Insgesamt mindestens 20 Urlaubstage geplant** (ohne Feiertage) pro Jahr - betriebliche Vorgabe
    - **Betrieblich**: **Deadline: 01.02. jedes Jahres** - Urlaub muss bis dahin für das laufende Jahr geplant sein - betriebliche Vorgabe
  - Wöchentliche Erinnerungsmails bei fehlenden Mindestanforderungen (bis Deadline)
  - Genehmigte Urlaubstage sind nicht mehr änderbar (User)
  - Admin kann genehmigte Urlaubsanträge löschen (aktualisiert Guthaben automatisch)
  - UI: Urlaubsplaner-Tab mit Jahr-Auswahl, Guthaben-Anzeige, Validierungshinweisen, Status-Übersicht
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
  - **Arbeitsstunden-Abgleich**: Gutgeschriebene Arbeitsstunden werden automatisch aus Stundenzetteln übernommen
  - **Automatische Verarbeitung**: Accounting Agent prüft Reisekosten im Verhältnis zu den Arbeitsstunden
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
  - **Reisekosten-Reports**: `TravelExpenseReportEntry` erweitert um `working_hours` (gutgeschriebene Arbeitsstunden)
  - **Reisekosten-Abgleich**: Arbeitsstunden werden automatisch aus Stundenzettel-Einträgen extrahiert und in Reports übernommen
  - **Accounting Agent**: Prüft Reisekosten im Verhältnis zu den Arbeitsstunden (Prompt aktualisiert)
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

