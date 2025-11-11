# 📘 Tick Guard - Benutzeranleitung

**Version:** 1.0  
**Stand:** 2025  
**Herausgeber:** Byte Commander

---

## 📑 Inhaltsverzeichnis

1. [Erste Schritte](#erste-schritte)
2. [Stundenzettel-App](#stundenzettel-app)
3. [Reisekosten-App](#reisekosten-app)
4. [Urlaubsplaner](#urlaubsplaner)
5. [Admin-Funktionen](#admin-funktionen)
6. [Buchhaltungs-Funktionen](#buchhaltungs-funktionen)
7. [Gesetzliche Hinweise](#gesetzliche-hinweise)
8. [Häufige Fragen (FAQ)](#häufige-fragen-faq)
9. [Kontakt & Support](#kontakt--support)

---

## Erste Schritte

### Anmeldung

1. Öffnen Sie Tick Guard in Ihrem Browser: **https://app.byte-commander.de**
2. Geben Sie Ihre **E-Mail-Adresse** und Ihr **Passwort** ein
3. Klicken Sie auf **"Anmelden"**

**Wichtig:** Bei der ersten Anmeldung müssen Sie die **Zwei-Faktor-Authentifizierung (2FA)** einrichten:
- Scannen Sie den QR-Code mit einer Authenticator-App (z.B. Google Authenticator, Microsoft Authenticator)
- Geben Sie den 6-stelligen Code aus der App ein
- Die 2FA ist **obligatorisch** und dient Ihrer Sicherheit

### Passwort zurücksetzen

Falls Sie Ihr Passwort vergessen haben:
1. Kontaktieren Sie Ihren Administrator
2. Der Administrator kann Ihr Passwort zurücksetzen
3. Nach dem Zurücksetzen müssen Sie ein neues Passwort setzen

### App-Auswahl

Nach der Anmeldung sehen Sie die **App-Auswahl**:
- **Stundenzettel App**: Für Zeiterfassung und Stundenzettel-Verwaltung
- **Reisekosten App**: Für Reisekostenabrechnungen
- **Urlaubsplaner**: Für Urlaubsanträge und -verwaltung

Klicken Sie auf die gewünschte App, um sie zu öffnen.

---

## Stundenzettel-App

### Übersicht

Die Stundenzettel-App ermöglicht es Ihnen, Ihre Arbeitszeiten wöchentlich zu erfassen und Stundenzettel zu erstellen.

### Neuen Stundenzettel erstellen

1. Klicken Sie auf **"Neuer Stundenzettel"**
2. Wählen Sie die **Woche** aus (Montag-Datum)
3. Das System zeigt automatisch die Woche von Montag bis Sonntag an

### Zeiteinträge hinzufügen

Für jeden Arbeitstag können Sie mehrere Einträge erfassen:

**Pflichtfelder:**
- **Datum**: Automatisch vorausgefüllt (kann geändert werden)
- **Startzeit**: z.B. "08:00"
- **Endzeit**: z.B. "17:00"
- **Pause**: Pausenzeit in Minuten (z.B. "60" für 1 Stunde)
- **Aufgaben**: Beschreibung Ihrer Tätigkeiten
- **Kunde/Projekt**: Name des Kunden oder Projekts
- **Ort**: Arbeitsort (z.B. "Büro", "Kunde vor Ort")

**Optionale Felder:**
- **Fahrzeit**: Fahrzeit in Minuten (z.B. "30" für 30 Minuten)
  - **Wichtig**: Nur die **Anreise zum Arbeitsort** wird als Arbeitszeit gewertet
  - Die **tägliche Fahrt Hotel-Kunde** ist **KEINE Arbeitszeit** und sollte nicht als Fahrzeit erfasst werden
- **Weiterberechnen**: Checkbox, um Fahrzeit zur Arbeitszeit hinzuzufügen (nur für Anreise zum Arbeitsort)
- **Fahrzeug**: Auswahl des genutzten Fahrzeugs (Standard: Wochenfahrzeug, kann pro Tag überschrieben werden)

**Beispiel:**
```
Datum: 2025-01-15
Startzeit: 08:00
Endzeit: 17:00
Pause: 60
Aufgaben: Software-Entwicklung, Code-Review
Kunde/Projekt: Projekt Alpha
Ort: Büro
Fahrzeit: 0 (nur Anreise zum Arbeitsort, nicht tägliche Fahrten Hotel-Kunde)
Fahrzeug: Firmenwagen (Poolfahrzeug)
```

### Fahrzeug auswählen

- Wählen Sie beim Anlegen des Stundenzettels zuerst das **Wochenfahrzeug** aus der Liste Ihrer zugeordneten Fahrzeuge sowie aller Poolfahrzeuge.
- Bei Bedarf können Sie in jedem Tageintrag ein **abweichendes Fahrzeug** auswählen (z.B. bei spontanen Fahrzeugwechseln).
- Wenn Sie kein Fahrzeug auswählen, bleibt das Feld leer und es wird angenommen, dass kein Firmenfahrzeug genutzt wurde.

### Abwesenheitstage eintragen

Für **Urlaub**, **Krankheit** oder **Feiertage**:

1. Wählen Sie den entsprechenden Tag
2. Aktivieren Sie **"Abwesenheit"**
3. Wählen Sie den Typ:
   - **Urlaub**: Genehmigter Urlaub (wird automatisch aus Urlaubsplaner übernommen)
   - **Krankheit**: Krankheitstag
   - **Feiertag**: Wird automatisch erkannt (nicht als Urlaub gezählt)

**Wichtig:** 
- Genehmigter Urlaub wird automatisch eingetragen (aus Urlaubsplaner)
- Feiertage werden automatisch erkannt und eingetragen
- Sie müssen Abwesenheitstage nicht manuell eintragen, wenn sie bereits genehmigt sind

### Stundenzettel speichern

1. Klicken Sie auf **"Speichern"**
2. Der Stundenzettel wird als **"Entwurf"** gespeichert
3. Sie können ihn später bearbeiten

### Stundenzettel senden

1. Öffnen Sie den Stundenzettel
2. Klicken Sie auf **"Senden"**
3. Der Stundenzettel wird an die Buchhaltung gesendet
4. Status ändert sich zu **"Gesendet"**

**Wichtig:** Nach dem Senden können Sie den Stundenzettel **nicht mehr bearbeiten**.

### Unterschriebenen Stundenzettel hochladen

**Gesetzliche Anforderung:** Stundenzettel müssen vom Kunden unterzeichnet sein, bevor Arbeitszeit gutgeschrieben wird.

1. Laden Sie den **vom Kunden unterzeichneten Stundenzettel** als PDF hoch
2. Klicken Sie auf **"Unterschriebenen Stundenzettel hochladen"**
3. Wählen Sie die PDF-Datei aus
4. Das System prüft automatisch die Unterschrift:
   - ✅ **Unterschrift verifiziert**: Stundenzettel wird automatisch genehmigt, Arbeitszeit wird gutgeschrieben
   - ⚠️ **Unterschrift nicht verifiziert**: Stundenzettel wird zur manuellen Prüfung an die Buchhaltung gesendet

**Status-Anzeige:**
- 🟢 **"Unterschrift verifiziert"**: Automatisch genehmigt
- 🟠 **"Unterschrift hochgeladen"**: Wird manuell geprüft

### Stundenzettel herunterladen

1. Öffnen Sie den Stundenzettel
2. Klicken Sie auf **"PDF herunterladen"**
3. Das PDF wird generiert und heruntergeladen
4. Eine Kopie wird automatisch per E-Mail an Sie und die Buchhaltung gesendet

### Stundenzettel löschen

**Nur möglich bei Status "Entwurf":**

1. Öffnen Sie den Stundenzettel
2. Klicken Sie auf **"Löschen"**
3. Bestätigen Sie die Löschung

**Wichtig:** Gesendete oder genehmigte Stundenzettel können **nicht gelöscht** werden (gesetzliche Aufbewahrungspflicht).

### Monatsstatistiken

1. Wählen Sie einen **Monat** aus
2. Das System zeigt:
   - Gesamtstunden im Monat
   - Stunden pro Woche
   - Rang im Team (wenn aktiviert)

---

## Reisekosten-App

### Übersicht

Die Reisekosten-App ermöglicht es Ihnen, Reisekostenabrechnungen zu erstellen und Belege hochzuladen.

### Neue Reisekostenabrechnung erstellen

1. Klicken Sie auf **"Neue Abrechnung"**
2. Wählen Sie den **Monat** aus (aktueller Monat + max. 2 Monate zurück)
3. Das System füllt automatisch aus:
   - **Tage mit Reisetätigkeit** (aus genehmigten Stundenzetteln)
   - **Arbeitsstunden** (aus genehmigten Stundenzetteln)
   - **Orte** (aus Stundenzetteln)
   - **Kunden/Projekte** (aus Stundenzetteln)

**Wichtig:** Nur Tage mit **genehmigten, unterschriebenen und verifizierten Stundenzetteln** werden berücksichtigt.

### Reiseeinträge prüfen

Alle relevanten Reisetage werden automatisch aus Ihren genehmigten Stundenzetteln übernommen. Sie müssen **keine manuellen Eingaben** vornehmen.

Die Liste zeigt für jeden Tag:

- **Datum**, **Ort** und **Kunde/Projekt**
- **Fahrzeit (Minuten)** und bereits erfasste **Arbeitsstunden**
- Hinweis, wenn für einen Tag noch keine Arbeitsstunden hinterlegt sind (z.B. nur Anreise)

> **Hinweis:** Fehlt ein genehmigter Stundenzettel, erscheint der Tag nicht in der Liste. Reichen Sie den entsprechenden Stundenzettel nach oder wenden Sie sich an die Buchhaltung.

### Belege hochladen

**Gesetzliche Anforderung:** Alle Reisekosten müssen mit Belegen dokumentiert werden (GoBD).

**Vereinfachte Bedienung:** Sie müssen nur PDF-Belege hochladen - alle Daten werden automatisch extrahiert!

1. Klicken Sie auf **"Beleg hochladen"** (Datei-Auswahl)
2. Wählen Sie die **PDF-Datei** des Belegs aus
3. Das System extrahiert automatisch:
   - **Betrag** aus dem Beleg
   - **Datum** aus dem Beleg
   - **Typ** (Hotel, Restaurant, Maut, Parken, Tanken, Bahn, etc.)
   - **Währung** (falls nicht EUR)
4. Der Beleg wird automatisch dem passenden Reiseeintrag zugeordnet (basierend auf Datum)
5. Die Datei wird verschlüsselt gespeichert (DSGVO-konform)

**Automatische Prüfung:**
- Das System prüft automatisch auf **Logik-Probleme**:
  - Überlappende Hotelrechnungen (mehrere Rechnungen für denselben Zeitraum)
  - Datum-Abgleich mit Arbeitsstunden (fehlende Arbeitsstunden im Stundenzettel)
  - Zeitliche Konsistenz (z.B. Übernachtung ohne Anreise)
  - Orts-Konsistenz (Hotel-Ort passt zu Reiseort)
  - Betrags-Plausibilität
- Bei Problemen wird automatisch der **Chat-Agent** aktiviert und informiert Sie

**Anzeige extrahierter Daten:**
- Nach dem Upload sehen Sie direkt:
  - Extrahierter **Betrag** und **Währung**
  - Extrahierter **Datum**
  - Erkannte **Kategorie** (Hotel, Restaurant, etc.)
  - **Hinweise** bei Problemen (rot markiert)

**Fremdwährungs-Nachweis:**
- Wenn eine **Fremdwährung** (nicht EUR) erkannt wird, müssen Sie einen **Nachweis über den tatsächlichen Euro-Betrag** hochladen
- **Akzeptierte Nachweise**: Kontoauszug, Bankbeleg, oder ähnliche Dokumente, die den tatsächlichen Euro-Betrag zeigen
- Der Nachweis wird **automatisch erkannt** und angezeigt, wenn eine Fremdwährung im Beleg gefunden wird
- Sie sehen eine **gelbe Warnung** mit Upload-Button für den Nachweis
- Nach erfolgreichem Upload wird der Nachweis als **✓ Nachweis hochgeladen** angezeigt

**Wichtig:**
- Nur **PDF-Dateien** sind erlaubt
- Maximale Dateigröße: **10 MB**
- Belege werden **verschlüsselt** gespeichert
- Belege werden in strukturierten Ordnern gespeichert: `User_Monat_ReportID/`
- **Keine manuellen Eingaben nötig** - alles wird automatisch extrahiert!
- **Fremdwährungs-Nachweis ist erforderlich** für alle Belege in Fremdwährung (GoBD)
- Sie können irrtümlich hochgeladene Belege im Status **"Entwurf"** jederzeit wieder entfernen

### Abrechnung einreichen

1. Überprüfen Sie alle Einträge und Belege
2. Klicken Sie auf **"Bericht einreichen"**
3. Das System prüft automatisch:
   - ✅ Für alle Tage liegt ein freigegebener, unterschriebener und verifizierter Stundenzettel vor
   - ✅ Alle Fremdwährungsbelege besitzen einen Nachweis
   - ⚠️ Fehlende Unterlagen werden als Fehlermeldung angezeigt
4. Nach erfolgreicher Prüfung wechselt der Status zu **"In Prüfung"**. Die Buchhaltung (und Agenten) übernehmen nun.

### Chat mit Agenten

Während der Prüfung können Sie mit den Agenten chatten:

1. Öffnen Sie die Abrechnung
2. Scrollen Sie zum **Chat-Bereich**
3. Stellen Sie Fragen oder beantworten Sie Rückfragen
4. Die Agenten helfen bei der Zuordnung und Prüfung

> **Tipp:** Antworten Sie zeitnah, damit Freigaben nicht verzögert werden. Jede Nachricht wird protokolliert.

### Statusübersicht

- **Entwurf (draft)**: Bericht kann bearbeitet, Belege hinzugefügt oder entfernt werden.
- **Übermittelt (submitted)** / **In Prüfung (in_review)**: Bericht wurde eingereicht; Buchhaltung und Agenten prüfen.
- **Freigegeben (approved)**: Reisekosten sind genehmigt.
- **Zurückgewiesen (rejected)**: Bericht wurde mit Begründung abgelehnt. Sie können nachbessern und erneut einreichen.

### Abrechnung bearbeiten/löschen

**Nur möglich bei Status "Entwurf":**

1. Öffnen Sie die Abrechnung
2. Klicken Sie auf **"Bearbeiten"** oder **"Löschen"**
3. Bestätigen Sie die Aktion

**Wichtig:** Eingereichte Abrechnungen können **nicht mehr bearbeitet** werden.

---

## Urlaubsplaner

### Übersicht

Der Urlaubsplaner ermöglicht es Ihnen, Urlaub zu beantragen und Ihren Urlaubsstand einzusehen.

### Urlaub beantragen

1. Wählen Sie das **Jahr** aus
2. Klicken Sie auf **"Neuer Urlaubsantrag"**
3. Geben Sie ein:
   - **Startdatum**: Erster Urlaubstag
   - **Enddatum**: Letzter Urlaubstag
   - **Notizen**: Optional (z.B. "Familienurlaub")
4. Klicken Sie auf **"Beantragen"**

**Automatische Berechnung:**
- Das System zählt nur **Werktage (Mo-Fr)** als Urlaubstage
- **Feiertage werden automatisch ausgeschlossen** (nicht als Urlaub gezählt)
- Die Anzahl der Urlaubstage wird automatisch berechnet

**Beispiel:**
```
Startdatum: 2025-07-01 (Montag)
Enddatum: 2025-07-14 (Sonntag)
→ 10 Werktage (ohne Feiertage)
```

### Urlaubsstand einsehen

1. Wählen Sie das **Jahr** aus
2. Das System zeigt:
   - **Gesamt**: Verfügbare Urlaubstage
   - **Verbraucht**: Bereits genehmigte Urlaubstage
   - **Verbleibend**: Noch verfügbare Urlaubstage

### Urlaubsanforderungen prüfen

Das System prüft automatisch, ob Sie die **gesetzlichen und betrieblichen Anforderungen** erfüllen:

**Gesetzliche Anforderung (Bundesurlaubsgesetz):**
- ✅ **Mindestens 2 Wochen am Stück** (10 Werktage, Mo-Fr ohne Feiertage) - **gesetzlicher Erholungsurlaub** (§7 BUrlG)

**Betriebliche Vorgaben:**
- ✅ **Insgesamt mindestens 20 Urlaubstage** geplant (ohne Feiertage) - betriebliche Vorgabe
- ✅ **Deadline: 01.02.** - Urlaub muss bis dahin für das laufende Jahr geplant sein - betriebliche Vorgabe

**Status-Anzeige:**
- 🟢 **"Anforderungen erfüllt"**: Alle Anforderungen sind erfüllt
- 🔴 **"Anforderungen nicht erfüllt"**: Mindestens eine Anforderung fehlt

**Wichtig:** 
- Die **2 Wochen am Stück** sind **gesetzlich vorgeschrieben** (Erholungsurlaub)
- Die **20 Tage verplant** und die **Deadline 01.02.** sind **betriebliche Vorgaben**
- Wenn Sie die Anforderungen nicht bis zum **01.02.** erfüllen, erhalten Sie wöchentlich eine Erinnerungs-E-Mail

### Urlaubsantrag löschen

**Nur möglich bei Status "Ausstehend":**

1. Öffnen Sie den Urlaubsantrag
2. Klicken Sie auf **"Löschen"**
3. Bestätigen Sie die Löschung

**Wichtig:** Genehmigte Urlaubsanträge können **nicht gelöscht** werden (nur durch Admin).

### Genehmigte Urlaubstage

Genehmigte Urlaubstage werden **automatisch** in Ihre Stundenzettel eingetragen:
- Sie müssen genehmigten Urlaub **nicht manuell** eintragen
- Die Tage erscheinen automatisch als "Urlaub" in den Stundenzetteln
- Sie können genehmigten Urlaub **nicht mehr ändern**

---

## Admin-Funktionen

### Benutzer verwalten

**Neuen Benutzer erstellen:**

1. Gehen Sie zu **"Benutzerverwaltung"**
2. Klicken Sie auf **"Neuer Benutzer"**
3. Geben Sie ein:
   - **E-Mail**: E-Mail-Adresse des Benutzers
   - **Name**: Vollständiger Name
   - **Passwort**: Temporäres Passwort (Benutzer muss es bei erster Anmeldung ändern)
   - **Rolle**: "User", "Accounting" oder "Admin"
   - **Wochenstunden**: Standard 40 Stunden
4. Klicken Sie auf **"Erstellen"**

**Benutzer bearbeiten:**

1. Öffnen Sie den Benutzer
2. Klicken Sie auf **"Bearbeiten"**
3. Ändern Sie die gewünschten Felder
4. Klicken Sie auf **"Speichern"**

**Benutzer löschen:**

1. Öffnen Sie den Benutzer
2. Klicken Sie auf **"Löschen"**
3. Bestätigen Sie die Löschung

**Wichtig:** Beim Löschen werden **alle zugehörigen Stundenzettel** ebenfalls gelöscht.

### Urlaubstage verwalten

**Urlaubstage pro Mitarbeiter eintragen:**

1. Gehen Sie zu **"Urlaubsplaner"**
2. Wählen Sie das **Jahr** aus
3. Scrollen Sie zu **"Urlaubstage-Verwaltung"**
4. Klicken Sie auf **"Bearbeiten"** bei einem Mitarbeiter
5. Geben Sie die **Gesamt-Urlaubstage** ein (z.B. "30")
6. Klicken Sie auf **"Speichern"**

**Genehmigten Urlaub löschen:**

1. Öffnen Sie den genehmigten Urlaubsantrag
2. Klicken Sie auf **"Admin-Löschen"**
3. Bestätigen Sie die Löschung
4. Das Urlaubsguthaben wird automatisch aktualisiert

### Ankündigungen erstellen

1. Gehen Sie zu **"Ankündigungen"**
2. Klicken Sie auf **"Neue Ankündigung"**
3. Geben Sie ein:
   - **Titel**: Überschrift
   - **Inhalt**: Text (HTML möglich)
   - **Bild**: Optional (Upload)
   - **Aktiv bis**: Ablaufdatum
4. Klicken Sie auf **"Erstellen"**

**Wichtig:** Ankündigungen werden auf der **App-Auswahlseite** angezeigt.

### Fahrzeuge verwalten

1. Gehen Sie zu **"Administration"** → **"Fahrzeuge"**
2. Tragen Sie ein:
   - **Bezeichnung** (z. B. „Transporter 1“)
   - **Kennzeichen**
   - Optional: Ordnen Sie das Fahrzeug einer Person zu
   - Alternativ markieren Sie das Fahrzeug als **Poolfahrzeug**
3. Klicken Sie auf **"Fahrzeug speichern"**
4. Bestehende Fahrzeuge können über **"Bearbeiten"** angepasst oder über **"Löschen"** entfernt werden

**Hinweise:**
- Poolfahrzeuge stehen allen Mitarbeitenden zur Verfügung (keine Zuordnung)
- Persönliche Fahrzeuge werden einer Person zugeordnet (z. B. Dienstwagen)
- Änderungen sind sofort aktiv und wirken sich auf kommende Reisekostenabrechnungen aus

### SMTP-Konfiguration

1. Gehen Sie zu **"Einstellungen"** → **"SMTP-Konfiguration"**
2. Geben Sie ein:
   - **SMTP-Server**: z.B. "mail.byte-commander.de"
   - **SMTP-Port**: z.B. "587"
   - **Benutzername**: E-Mail-Adresse
   - **Passwort**: E-Mail-Passwort
   - **Admin-E-Mail**: E-Mail für Benachrichtigungen
3. Klicken Sie auf **"Speichern"**

**Testen:**
- Klicken Sie auf **"Test-E-Mail senden"**
- Prüfen Sie, ob die E-Mail ankommt

---

## Buchhaltungs-Funktionen

### Stundenzettel genehmigen

**Automatische Genehmigung:**
- Wenn der Dokumenten-Agent die Unterschrift verifiziert, wird der Stundenzettel **automatisch genehmigt**
- Sie erhalten eine E-Mail-Benachrichtigung

**Manuelle Genehmigung (nur in Ausnahmefällen):**

1. Öffnen Sie den Stundenzettel
2. Prüfen Sie:
   - ✅ Unterschrift vorhanden (auch wenn Agent nicht verifizieren konnte)
   - ✅ Oder nur Abwesenheitstage (Urlaub/Krankheit/Feiertag) ohne Arbeitszeit
3. Klicken Sie auf **"Genehmigen"**
4. Der Stundenzettel wird genehmigt und Arbeitszeit wird gutgeschrieben

**Wichtig:** 
- Manuelle Genehmigung ist nur möglich, wenn:
  - Agent konnte Unterschrift nicht verifizieren (aber Unterschrift vorhanden)
  - Oder nur Abwesenheitstage (keine Arbeitszeit)
- Stundenzettel mit Arbeitszeit **ohne Unterschrift** können **nicht genehmigt** werden

### Stundenzettel ablehnen

1. Öffnen Sie den Stundenzettel
2. Klicken Sie auf **"Ablehnen"**
3. Geben Sie einen **Grund** ein
4. Klicken Sie auf **"Bestätigen"**
5. Der Benutzer wird benachrichtigt

### Reisekostenabrechnungen prüfen

1. Öffnen Sie die Abrechnung
2. Das System prüft automatisch mit KI-Agenten:
   - **Dokumentenanalyse**: Belege werden analysiert
   - **Zuordnung**: Kosten werden Kategorien zugeordnet
   - **Plausibilität**: Prüfung im Verhältnis zu Arbeitsstunden
3. Die Agenten stellen bei Bedarf **Rückfragen** im Chat
4. Prüfen Sie die Hinweise im Bereich **"Belege & Dokumente"** sowie die Chat-Nachrichten
5. Nach der Prüfung können Sie:
   - **Genehmigen**: Abrechnung wird freigegeben (Status **"Freigegeben"**)
   - **Zurückweisen**: Abrechnung wird mit optionalem Grund zurückgewiesen (Status **"Zurückgewiesen"**)
6. Bei Bedarf laden Sie eigene Chat-Nachrichten hoch (z.B. Rückfragen an den Mitarbeiter)

### Monatsberichte

1. Gehen Sie zu **"Buchhaltung"** → **"Monatsberichte"**
2. Wählen Sie einen **Monat** aus
3. Das System zeigt:
   - Gesamtstunden aller Mitarbeiter
   - Stunden pro Mitarbeiter
   - Genehmigte Stundenzettel
   - Reisekostenabrechnungen
4. Klicken Sie auf **"PDF herunterladen"** für einen Bericht

### Urlaubsanträge genehmigen/ablehnen

1. Gehen Sie zu **"Urlaubsplaner"**
2. Scrollen Sie zu **"Ausstehende Anträge"**
3. Öffnen Sie einen Antrag
4. Klicken Sie auf **"Genehmigen"** oder **"Ablehnen"**
5. Bei Genehmigung wird das Urlaubsguthaben automatisch aktualisiert

---

## Gesetzliche Hinweise

### Arbeitszeitgesetz (ArbZG)

**Wichtige Regelungen:**
- **Höchstarbeitszeit**: 8 Stunden pro Tag (kann auf 10 Stunden verlängert werden, wenn innerhalb von 6 Monaten im Durchschnitt 8 Stunden nicht überschritten werden)
- **Ruhezeiten**: Mindestens 11 Stunden Ruhezeit zwischen Arbeitsende und Arbeitsbeginn
- **Pausen**: Bei mehr als 6 Stunden Arbeit mindestens 30 Minuten Pause, bei mehr als 9 Stunden mindestens 45 Minuten

**In Tick Guard:**
- Pausen werden automatisch von der Arbeitszeit abgezogen
- Das System warnt bei Überschreitung der Höchstarbeitszeit
- Ruhezeiten werden nicht automatisch geprüft (manuelle Überwachung erforderlich)

### GoBD (Grundsätze zur ordnungsmäßigen Führung und Aufbewahrung von Büchern, Aufzeichnungen und Belegen)

**Aufbewahrungsfristen:**
- **Reisekostenbelege**: 10 Jahre
- **Stundenzettel**: 10 Jahre (wenn steuerlich relevant)
- **Genehmigte Abrechnungen**: 10 Jahre

**In Tick Guard:**
- Alle Dokumente werden **verschlüsselt** gespeichert
- Automatische **Retention-Management**: Dokumente werden nach Ablauf der Aufbewahrungsfrist gelöscht
- **Audit-Logging**: Alle Zugriffe werden protokolliert

### DSGVO (Datenschutz-Grundverordnung)

**Ihre Rechte:**
- **Auskunftsrecht**: Sie können Auskunft über gespeicherte Daten verlangen
- **Löschungsrecht**: Sie können Löschung Ihrer Daten verlangen (außer bei gesetzlichen Aufbewahrungspflichten)
- **Widerspruchsrecht**: Sie können der Verarbeitung widersprechen
- **Datenübertragbarkeit**: Sie können Ihre Daten in einem strukturierten Format erhalten

**In Tick Guard:**
- Alle persönlichen Daten werden **verschlüsselt** gespeichert
- **Zugriffskontrolle**: Nur autorisierte Personen haben Zugriff
- **Audit-Logging**: Alle Zugriffe werden protokolliert
- **Minimierung**: Es werden nur notwendige Daten gespeichert

**Kontakt für Datenschutz-Anfragen:**
- E-Mail: datenschutz@app.byte-commander.de
- Adresse: Byte Commander

### EU-AI-Act (Künstliche Intelligenz Gesetz)

**Transparenz:**
- Tick Guard nutzt **KI-Agenten** für die automatische Prüfung von Dokumenten
- Alle KI-Entscheidungen werden **protokolliert**
- Sie haben das Recht, **Auskunft** über KI-Entscheidungen zu erhalten

**In Tick Guard:**
- **Dokumenten-Agent**: Prüft automatisch Unterschriften auf Stundenzetteln
- **Buchhaltungs-Agent**: Prüft Reisekostenabrechnungen
- **Chat-Agent**: Beantwortet Fragen
- Alle Agenten-Entscheidungen werden **transparent** dokumentiert

### Urlaubsrecht

**Gesetzliche Anforderung (Bundesurlaubsgesetz - BUrlG):**
- **Mindestens 2 Wochen am Stück** (10 Werktage, Mo-Fr ohne Feiertage) - **gesetzlicher Erholungsurlaub** (§7 BUrlG)
  - Der Erholungsurlaub muss zusammenhängend gewährt werden, wenn der Arbeitnehmer dies wünscht
  - Mindestens 12 Werktage müssen zusammenhängend gewährt werden (bei 6-Tage-Woche)
  - Bei 5-Tage-Woche entspricht dies mindestens 10 Werktagen (2 Wochen)

**Betriebliche Vorgaben (nicht gesetzlich):**
- **Insgesamt mindestens 20 Urlaubstage** pro Jahr geplant - betriebliche Vorgabe
- **Deadline: 01.02.** - Urlaub muss bis dahin für das laufende Jahr geplant sein - betriebliche Vorgabe

**In Tick Guard:**
- Das System prüft automatisch, ob Sie die **gesetzlichen und betrieblichen Anforderungen** erfüllen
- **Feiertage werden automatisch ausgeschlossen** (nicht als Urlaub gezählt)
- Bei fehlenden Anforderungen erhalten Sie **wöchentliche Erinnerungs-E-Mails**

### Steuerrecht (Reisekosten)

**Abzugsfähige Reisekosten:**
- **Fahrkosten**: Fahrtkosten zur ersten Tätigkeitsstätte (nicht abzugsfähig), zu anderen Tätigkeitsstätten (abzugsfähig)
- **Übernachtungskosten**: Abzugsfähig bei Dienstreisen
- **Verpflegungsmehraufwand**: Pauschale Spesensätze (abhängig vom Land)
- **Sonstige Kosten**: z.B. Parkgebühren, Maut

**In Tick Guard:**
- Spesensätze werden **automatisch** berechnet (basierend auf Land)
- **Belege sind erforderlich** für alle Kosten (GoBD)
- Alle Belege werden **verschlüsselt** gespeichert

---

## Häufige Fragen (FAQ)

### Allgemein

**F: Wie ändere ich mein Passwort?**
A: Kontaktieren Sie Ihren Administrator. Nach dem Zurücksetzen müssen Sie ein neues Passwort setzen.

**F: Was ist 2FA und warum ist es obligatorisch?**
A: 2FA (Zwei-Faktor-Authentifizierung) ist eine zusätzliche Sicherheitsebene. Sie müssen bei jeder Anmeldung einen Code aus einer Authenticator-App eingeben. Dies schützt Ihr Konto vor unbefugtem Zugriff.

**F: Kann ich die App auf meinem Smartphone nutzen?**
A: Ja, Tick Guard ist eine **PWA (Progressive Web App)**. Sie können die App auf Ihrem Smartphone installieren:
- **iOS**: Safari → Teilen → Zum Home-Bildschirm
- **Android**: Chrome → Menü → Zum Startbildschirm hinzufügen

### Stundenzettel

**F: Warum kann ich meinen Stundenzettel nicht mehr bearbeiten?**
A: Nach dem **"Senden"** können Stundenzettel nicht mehr bearbeitet werden (gesetzliche Aufbewahrungspflicht). Bitte prüfen Sie Ihre Einträge vor dem Senden.

**F: Warum wird mein Stundenzettel nicht automatisch genehmigt?**
A: Der Dokumenten-Agent konnte die Unterschrift nicht automatisch verifizieren. Die Buchhaltung prüft den Stundenzettel manuell. Stellen Sie sicher, dass der Stundenzettel **vom Kunden unterzeichnet** ist.

**F: Wie zähle ich Fahrzeit?**
A: Geben Sie die Fahrzeit in Minuten ein (z.B. "30" für 30 Minuten). Aktivieren Sie **"Weiterberechnen"**, um die Fahrzeit zur Arbeitszeit hinzuzufügen.

**Wichtig:** 
- Nur die **Anreise zum Arbeitsort** wird als Arbeitszeit gewertet
- Die **tägliche Fahrt Hotel-Kunde** ist **KEINE Arbeitszeit** und sollte nicht als Fahrzeit erfasst werden
- Beispiel: Wenn Sie von zu Hause zum Kunden fahren (Anreise), zählt diese Fahrzeit. Die tägliche Fahrt vom Hotel zum Kunden zählt nicht.

**F: Werden Feiertage automatisch erkannt?**
A: Ja, deutsche Feiertage (bundesweit) und sächsische Feiertage werden automatisch erkannt und als "Feiertag" eingetragen. Feiertage werden **nicht als Urlaub** gezählt.

### Reisekosten

**F: Warum kann ich meine Abrechnung nicht einreichen?**
A: Für alle Tage in der Abrechnung müssen **genehmigte, unterschriebene und verifizierte Stundenzettel** vorhanden sein. Prüfen Sie die **"Fehlenden Tage"** in der Übersicht.

**F: Welche Belege benötige ich?**
A: Alle Reisekosten müssen mit **Belegen** dokumentiert werden (GoBD):
- Fahrkosten: Tankbeleg, Bahnticket, etc.
- Übernachtung: Hotelrechnung
- Verpflegung: Spesensätze (automatisch berechnet)
- Sonstige: Parkgebühren, Maut, etc.

**F: Wie groß dürfen Belege sein?**
A: Maximale Dateigröße: **10 MB**. Nur **PDF-Dateien** sind erlaubt.

**F: Werden meine Belege sicher gespeichert?**
A: Ja, alle Belege werden **verschlüsselt** gespeichert (DSGVO-konform) und in strukturierten Ordnern organisiert.

### Urlaub

**F: Warum muss ich 2 Wochen am Stück Urlaub nehmen?**
A: Das ist eine **gesetzliche Anforderung** nach dem Bundesurlaubsgesetz (BUrlG §7 - Erholungsurlaub). Mindestens 2 Wochen (10 Werktage bei 5-Tage-Woche) müssen am Stück genommen werden, um eine ausreichende Erholung zu gewährleisten.

**F: Warum müssen 20 Tage bis zum 01.02. verplant sein?**
A: Das ist eine **betriebliche Vorgabe** (nicht gesetzlich). Sie dient der besseren Planbarkeit und Organisation. Die gesetzliche Anforderung ist nur, dass mindestens 2 Wochen am Stück genommen werden müssen.

**F: Warum werden Feiertage nicht als Urlaub gezählt?**
A: Feiertage sind **keine Urlaubstage** (gesetzlich). Sie werden automatisch erkannt und ausgeschlossen.

**F: Was passiert, wenn ich die Urlaubsanforderungen nicht erfülle?**
A: Sie erhalten **wöchentliche Erinnerungs-E-Mails**, bis Sie die Anforderungen erfüllen. Die Deadline ist der **01.02.** jedes Jahres.

**F: Kann ich genehmigten Urlaub ändern?**
A: Nein, genehmigter Urlaub kann **nicht mehr geändert** werden. Kontaktieren Sie Ihren Administrator, wenn eine Änderung notwendig ist.

---

## Kontakt & Support

### Technischer Support

**E-Mail:** support@app.byte-commander.de  
**Website:** https://app.byte-commander.de

### Datenschutz

**E-Mail:** datenschutz@app.byte-commander.de

### Administrator

**E-Mail:** admin@schmitz-intralogistik.de  
*(Legacy: admin@app.byte-commander.de)*

---

## Anhang

### Tastenkürzel

- **Strg + S**: Speichern (in Formularen)
- **Esc**: Dialog schließen
- **Enter**: Formular absenden

### Browser-Kompatibilität

**Empfohlene Browser:**
- Chrome/Edge (neueste Version)
- Firefox (neueste Version)
- Safari (neueste Version)

**Nicht unterstützt:**
- Internet Explorer
- Ältere Browser-Versionen

### Systemanforderungen

- **Internetverbindung**: Erforderlich
- **JavaScript**: Muss aktiviert sein
- **Cookies**: Werden für die Authentifizierung verwendet
- **Bildschirmauflösung**: Mindestens 320px Breite (Mobile)

---

**Letzte Aktualisierung:** 2025  
**Version:** 1.0  
**Herausgeber:** Byte Commander

---

## Rechtliche Hinweise

Diese Software wird von Byte Commander bereitgestellt. Die Nutzung erfolgt auf eigene Verantwortung. Byte Commander übernimmt keine Haftung für Fehler oder Ausfälle.

**Lizenz:** Proprietär - Alle Rechte vorbehalten.

**Datenschutz:** Bitte beachten Sie unsere Datenschutzerklärung unter https://app.byte-commander.de/datenschutz

**Impressum:** Byte Commander

---

**© 2025 Byte Commander - Tick Guard**

