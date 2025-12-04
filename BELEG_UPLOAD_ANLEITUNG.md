# Beleg-Upload Anleitung

## Übersicht: Wo können Belege hochgeladen werden?

Es gibt **zwei verschiedene Möglichkeiten**, Belege (z.B. Hotelrechnungen) hochzuladen:

### 1. **Reisekosten-Einzelausgaben** (`/app/expenses/individual`)

**Zweck:** Einzelne Reisekosten-Ausgaben mit Belegen verwalten

**Verwendung:**
- Für einzelne Ausgaben (z.B. eine Hotelrechnung, ein Bahnticket)
- Jede Ausgabe kann mehrere Belege haben
- Belege werden direkt der Ausgabe zugeordnet

**Workflow:**
1. Navigiere zu **"Reisekosten" → "Einzelausgaben"**
2. Klicke auf **"Neue Ausgabe"**
3. Fülle aus:
   - Datum
   - Kunde/Projekt (optional)
   - Kommentar (z.B. "Hotel Berlin")
4. Klicke auf **"Erstellen"**
5. Nach dem Erstellen erscheint die neue Ausgabe in der Liste
6. Klicke auf **"Beleg hochladen"** bei der erstellten Ausgabe
7. Wähle eine PDF-Datei aus (z.B. Hotelrechnung)
8. Der Beleg wird hochgeladen und analysiert

**Beleg-Upload:**
- Nur bei Ausgaben mit Status "Entwurf" möglich
- PDF-Format erforderlich
- Automatische Verschlüsselung (DSGVO-konform)
- Belege werden lokal auf dem Bürorechner gespeichert

---

### 2. **Reisekosten-Berichte** (`/app/expenses/reports/:id`)

**Zweck:** Monatliche Reisekosten-Berichte mit mehreren Belegen

**Verwendung:**
- Für monatliche Abrechnungen
- Mehrere Belege pro Monat
- Automatische Prüfung durch Agenten
- Validierung gegen Stundenzettel

**Workflow:**
1. Navigiere zu **"Reisekosten" → "Übersicht"**
2. Wähle einen Monat aus (z.B. "2025-01")
3. Klicke auf **"Bericht initialisieren"**
4. Der Bericht wird erstellt und geöffnet
5. Im Bereich **"Belege & Dokumente"**:
   - Klicke auf **"Datei auswählen"**
   - Wähle eine PDF-Datei (z.B. Hotelrechnung)
   - Der Beleg wird hochgeladen
6. Der Agent prüft automatisch:
   - Ob das Datum zum Monat passt
   - Bei Hotelrechnungen: Ob Zeiträume (date_from, date_to) zu Stundenzetteln passen
   - Vollständigkeit und Gültigkeit

**Beleg-Upload:**
- Nur bei Berichten mit Status "Entwurf" möglich
- PDF-Format erforderlich
- Automatische Analyse durch Document Agent
- Validierung gegen Stundenzettel
- Chat mit Agenten bei Problemen möglich

---

## Welche Möglichkeit sollte ich verwenden?

### **Reisekosten-Einzelausgaben** verwenden, wenn:
- ✅ Du einzelne Ausgaben schnell erfassen willst
- ✅ Du Belege direkt einer Ausgabe zuordnen willst
- ✅ Du keine monatliche Abrechnung brauchst
- ✅ Du flexibel arbeiten willst

### **Reisekosten-Berichte** verwenden, wenn:
- ✅ Du monatliche Abrechnungen machst
- ✅ Du mehrere Belege pro Monat hast
- ✅ Du automatische Prüfung durch Agenten willst
- ✅ Du Validierung gegen Stundenzettel brauchst
- ✅ Du Chat mit Agenten bei Fragen willst

---

## Häufige Fragen

### Kann ich Belege auch nachträglich hochladen?

**Ja**, solange die Ausgabe/Bericht den Status "Entwurf" hat:
- Bei Einzelausgaben: Klicke auf "Beleg hochladen" bei der Ausgabe
- Bei Berichten: Nutze den Upload-Button im Bereich "Belege & Dokumente"

### Was passiert mit den Belegen?

1. **Upload:** PDF wird hochgeladen
2. **Verschlüsselung:** Automatische Verschlüsselung (DSGVO-konform)
3. **Speicherung:** Lokal auf dem Bürorechner (nicht auf dem Webserver)
4. **Analyse:** Document Agent analysiert den Beleg
5. **Validierung:** Prüfung gegen Stundenzettel (bei Berichten)

### Kann ich Belege löschen?

**Ja**, solange die Ausgabe/Bericht den Status "Entwurf" hat:
- Bei Einzelausgaben: Klicke auf "×" bei dem Beleg
- Bei Berichten: Nutze den "Löschen"-Button bei dem Beleg

### Welche Dateiformate werden unterstützt?

- **PDF** (empfohlen)
- Maximale Dateigröße: 10 MB

### Wo werden die Belege gespeichert?

- **Lokal auf dem Bürorechner** (nicht auf dem Webserver)
- Pfad: `/var/tick-guard/receipts/reisekosten_einzel/` (für Einzelausgaben)
- Pfad: `/var/tick-guard/receipts/reisekosten_berichte/` (für Berichte)
- Verschlüsselt gespeichert (DSGVO-konform)

---

## Troubleshooting

### "not found" Fehler beim Erstellen einer Einzelausgabe

**Mögliche Ursachen:**
1. Backend-Endpunkt nicht erreichbar
2. API-URL falsch konfiguriert
3. Authentifizierung fehlgeschlagen

**Lösung:**
- Prüfe Browser-Console (F12) auf Fehler
- Prüfe Backend-Logs: `journalctl -u tick-guard-backend -n 50`
- Prüfe ob Backend läuft: `systemctl status tick-guard-backend`

### Beleg-Upload funktioniert nicht

**Mögliche Ursachen:**
1. Ausgabe/Bericht hat nicht den Status "Entwurf"
2. Datei ist zu groß (>10 MB)
3. Datei ist kein PDF

**Lösung:**
- Prüfe den Status der Ausgabe/Bericht
- Reduziere Dateigröße oder konvertiere zu PDF
- Prüfe Browser-Console auf Fehler

---

## Zusammenfassung

**Zwei Möglichkeiten für Beleg-Upload:**

1. **Einzelausgaben** (`/app/expenses/individual`)
   - Schnell, flexibel
   - Direkte Zuordnung zu Ausgaben
   - Keine automatische Validierung

2. **Berichte** (`/app/expenses/reports/:id`)
   - Monatliche Abrechnungen
   - Automatische Prüfung durch Agenten
   - Validierung gegen Stundenzettel
   - Chat mit Agenten

**Beide Möglichkeiten sind DSGVO-konform:**
- Verschlüsselte Speicherung
- Lokale Speicherung (nicht auf Webserver)
- Audit-Logging

