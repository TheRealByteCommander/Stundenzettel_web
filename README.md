# Tick Guard - Zeiterfassung & Reisekosten-Management

Tick Guard - Professionelles Zeiterfassungs- und Reisekosten-Management-System von Byte Commander.

## 📘 Benutzeranleitung

**👉 [Benutzeranleitung (BENUTZERANLEITUNG.md)](BENUTZERANLEITUNG.md)** - Vollständige Anleitung für alle Benutzer mit detaillierten Erklärungen zu allen Funktionen, gesetzlichen Hinweisen und FAQs.

## Features

### Stundenzettel-App
- ✅ Wochenbasierte Zeiterfassung
- ✅ PDF-Generierung für Stundenzettel
- ✅ E-Mail-Versand mit PDF-Anhang
- ✅ Urlaub, Krankheit, Feiertag-Tracking
- ✅ Fahrzeit-Erfassung mit optionaler Weiterberechnung (nur Anreise zum Arbeitsort, nicht tägliche Fahrt Hotel-Kunde)
- ✅ Monatsstatistiken und Rang-System
- ✅ **Automatische Genehmigung durch Agent**: Wenn Dokumenten-Agent die Unterschrift verifiziert, wird automatisch als Arbeitszeit gutgeschrieben
- ✅ **Buchhaltung genehmigt nur in Ausnahmefällen**: Wenn Agent Unterschrift nicht verifizieren konnte oder nur Abwesenheitstage
- ✅ **Upload unterschriebener Stundenzettel** (vom Kunden unterzeichnet, vom User hochgeladen)
- ✅ **Automatische Verifikation der Unterschrift** durch Dokumenten-Agent (PDF-Text-Analyse)
- ✅ **Stunden werden nur aus verifizierten, unterschriebenen und genehmigten Stundenzetteln gezählt**
- ✅ **Urlaubsplaner**: Urlaub beantragen, Genehmigung, automatischer Eintrag in Stundenzettel

### Reisekosten-App
- ✅ **Vereinfachte Bedienung**: User lädt nur PDF-Belege hoch - alle Daten werden automatisch extrahiert
- ✅ **Automatische Datenextraktion**: 
  - Betrag, Datum, Typ, Währung werden automatisch aus PDFs extrahiert
  - Automatische Zuordnung zu Reiseeinträgen basierend auf Datum
  - Keine manuellen Eingaben mehr nötig
- ✅ **Logik- und Machbarkeitsprüfung**:
  - Überlappende Hotelrechnungen werden automatisch erkannt
  - Datum-Abgleich mit Arbeitsstunden aus Stundenzetteln
  - Zeitliche Konsistenz-Prüfung (z.B. Übernachtung ohne Anreise)
  - Orts-Konsistenz-Prüfung
  - Betrags-Plausibilitäts-Prüfung
- ✅ **Fremdwährungs-Nachweis**: Bei Fremdwährungen muss ein Nachweis über den tatsächlichen Euro-Betrag hochgeladen werden (z.B. Kontoauszug)
- ✅ Automatische Befüllung aus genehmigten, **verifizierten** Stundenzetteln
- ✅ **Arbeitsstunden-Abgleich**: Gutgeschriebene Arbeitsstunden aus Stundenzetteln werden automatisch in Reisekosten-Reports übernommen
- ✅ **Automatische Verarbeitung**: Accounting Agent prüft Reisekosten im Verhältnis zu den Arbeitsstunden
- ✅ PDF-Beleg-Upload (lokale Speicherung, DSGVO-konform)
- ✅ Monatsbasierte Abrechnungen (aktueller + 2 Monate zurück)
- ✅ **Chat-System für Klärung**: Bei Problemen oder offenen Punkten wird automatisch der Chat-Agent aktiviert
- ✅ Status-Management (Entwurf, In Prüfung, Genehmigt)
- ✅ **Validierung vor Einreichen**: Prüfung, ob alle Tage verifizierte Stundenzettel haben
- ✅ **Übersicht abgedeckte/fehlende Tage** in der UI
- ✅ **Reisekosten nur für verifizierte Stundenzettel** - fehlende Tage werden nicht berücksichtigt
- ✅ Automatische Prüfung mit Ollama LLM-Agenten
  - Dokumentenanalyse (OCR, Kategorisierung, Validierung, **Logik-Prüfung**)
  - **Automatische Verifikation unterschriebener Stundenzettel** (PDF-Text-Analyse)
  - Buchhaltungszuordnung (Verpflegungsmehraufwand, Spesensätze, **Machbarkeitsprüfung**)
  - Chat-Agent für Rückfragen und Klärung
  - **Memory-System**: Agenten lernen aus früheren Erfahrungen (bis zu 10.000 Einträge pro Agent)
  - **Web-Tools**: Zugriff auf aktuelle Daten
    - Aktuelle Spesensätze aus dem Internet
    - Währungswechselkurse in Echtzeit
    - Geocoding für Länderbestimmung
    - Web-Suche für aktuelle Informationen

### Urlaubsplaner-App
- ✅ **Urlaubsanträge stellen**: User können Urlaub beantragen (Start-/Enddatum)
- ✅ **Automatische Werktage-Berechnung**: System zählt nur Mo-Fr als Urlaubstage, **Feiertage werden automatisch ausgeschlossen**
- ✅ **Feiertags-Integration**: 
  - Deutsche Feiertage (bundesweit) und sächsische Feiertage werden automatisch erkannt
  - Feiertage werden **nicht als Urlaubstage gezählt**
  - Feiertage werden automatisch als "Feiertag" in Stundenzettel eingetragen
  - Feiertage sind programmweit verfügbar und werden automatisch genutzt
- ✅ **Genehmigung durch Admin/Buchhaltung**: Genehmigung/Ablehnung von Anträgen
- ✅ **Urlaubstage-Verwaltung**: Admin kann verfügbare Urlaubstage pro Mitarbeiter eintragen (Mo-Fr)
- ✅ **Automatischer Eintrag in Stundenzettel**: 
  - Genehmigte Urlaubstage werden automatisch als "Urlaub" eingetragen
  - Feiertage werden automatisch als "Feiertag" eingetragen (auch ohne genehmigten Urlaub)
- ✅ **Validierung und Anforderungen**: 
  - **Gesetzlich (Bundesurlaubsgesetz)**: **Mindestens 2 Wochen am Stück** (10 Werktage, Mo-Fr ohne Feiertage) - gesetzlicher Erholungsurlaub (§7 BUrlG)
  - **Betrieblich**: **Insgesamt mindestens 20 Urlaubstage geplant** (ohne Feiertage) pro Jahr - betriebliche Vorgabe
  - **Betrieblich**: **Deadline: 01.02. jedes Jahres** - Urlaub muss bis dahin für das laufende Jahr geplant sein - betriebliche Vorgabe
- ✅ **Wöchentliche Erinnerungsmails**: Automatische Erinnerung an User, die Mindestanforderungen noch nicht erfüllt haben
- ✅ **Nicht mehr änderbar**: Genehmigte Urlaubstage können vom User nicht mehr verändert werden
- ✅ **Admin-Löschung**: Admin kann genehmigte Urlaubsanträge löschen (Guthaben wird aktualisiert)

### Weitere Features
- ✅ Benutzer- und Adminverwaltung mit Rollen (User, Admin, Buchhaltung)
- ✅ Obligatorische 2FA (Google Authenticator)
- ✅ Ankündigungen/News-System mit Bildern
- ✅ Mobile-First Responsive Web-Interface
- ✅ PWA-Support (Installierbar auf Mobilgeräten)
- ✅ DSGVO & EU-AI-Act Compliance
  - Datenverschlüsselung (Fernet/AES-128)
  - Audit-Logging
  - Retention-Management
  - AI-Transparenz
- ✅ Datenbank-Migrations-Tool (Import aus Vorgänger-Version)
- ✅ LLM-Integration für Proxmox (Agents auf Proxmox, LLMs auf GMKTec evo x2)

## 📘 Installationsanleitungen

**⚠️ WICHTIG: Architektur-Verständnis**

Diese Anwendung besteht aus mehreren Komponenten, die auf verschiedenen Servern laufen:

- ✅ **Frontend:** All-inkl.com Webserver (nur statische Dateien aus React Build)
- ✅ **Backend:** Proxmox Server (Python/FastAPI) - **NICHT auf All-inkl!**
- ✅ **MongoDB:** Proxmox Server (oder remote)
- ✅ **Agents:** Proxmox Server (laufen mit Backend zusammen, kein separater Service)
- ✅ **Ollama (LLM):** GMKTec evo x2 (Home-Netzwerk)

### 📚 Installationsanleitungen

- **⭐ KORREKTE Installationsanleitung:** Siehe **[INSTALLATION_COMPLETE_CORRECT.md](INSTALLATION_COMPLETE_CORRECT.md)** - Vollständige, korrekte Anleitung mit klarer Beschreibung wo was installiert wird
- **Architektur-Details:** Siehe **[ARCHITEKTUR_ALL_INKL_PROXMOX.md](ARCHITEKTUR_ALL_INKL_PROXMOX.md)** - Ihre spezifische Architektur
- **LLM-Integration:** Siehe **[backend/LLM_INTEGRATION.md](backend/LLM_INTEGRATION.md)** - Ollama Setup auf GMKTec
- **Legacy PHP-Version:** Siehe **[INSTALLATION_ALL_INKL.md](INSTALLATION_ALL_INKL.md)** - Nur für PHP-Version (Legacy)
- **Für Windows:** Siehe **[WINDOWS_INSTALLATION.md](WINDOWS_INSTALLATION.md)** - Windows-spezifische Anleitung
- **Für andere Server:** Siehe **[INSTALLATION_COMPLETE.md](INSTALLATION_COMPLETE.md)** - Allgemeine Installationsanleitung
- **Schnellstart:** Siehe **[QUICK_START.md](QUICK_START.md)**
- **Frontend Dependency-Fixes:** Siehe **[frontend/INSTALLATION_FIX.md](frontend/INSTALLATION_FIX.md)**
- **Office-Rechner Routing:** Siehe **[OFFICE_RECHNER_ROUTING.md](OFFICE_RECHNER_ROUTING.md)** - Lösungen für dynamische IPs

## ⚠️ Installation auf All-Inkl.com Webserver - NUR Frontend!

### ⚠️ WICHTIG: Diese Anleitung ist für die Legacy PHP-Version (nicht empfohlen)

**Für die aktuelle Architektur (Python/FastAPI + Agents + LLM):**
- ✅ **Frontend:** All-inkl.com (nur statische Dateien aus React Build)
- ✅ **Backend:** Proxmox Server (Python/FastAPI) - **NICHT auf All-inkl!**
- ✅ **MongoDB:** Proxmox Server (oder remote) - **NICHT MySQL auf All-inkl!**
- ✅ **Agents:** Proxmox Server (laufen mit Backend zusammen)
- ✅ **Ollama:** GMKTec evo x2 (Home-Netzwerk)

**Siehe `INSTALLATION_COMPLETE_CORRECT.md` für die vollständige, korrekte Installationsanleitung!**

---

### ❌ MySQL auf All-inkl.com ist NICHT notwendig für die aktuelle Architektur!

**MySQL wird nur verwendet für:**
1. **Migration:** Import aus alter MySQL-Datenbank (einmalig, via Migration-Tool)
2. **Legacy PHP-Version:** Falls Sie die PHP-Version aus `webapp/` verwenden (nicht empfohlen, nicht aktuell)

**Die aktuelle Python/FastAPI-Version nutzt NUR MongoDB:**
- MongoDB läuft auf Proxmox (oder remote/Cloud)
- Keine MySQL-Datenbank nötig für die aktuelle Architektur
- Keine Datenbank auf All-inkl.com nötig

---

### ✅ Frontend auf All-inkl.com installieren (Kurzanleitung)

**NUR für Frontend (statische Dateien):**

1. **Frontend lokal bauen:**
```bash
cd frontend/
npm install
# .env Datei erstellen:
echo "REACT_APP_BACKEND_URL=https://proxmox-domain.de:8000" > .env
npm run build
```

2. **Frontend-Dateien hochladen:**
   - Inhalt von `frontend/build/` auf All-inkl hochladen
   - `.htaccess` für React Router hochladen

3. **Fertig!** Backend läuft auf Proxmox, nicht auf All-inkl.

---

### ❌ Legacy PHP-Version (nur falls Sie wirklich PHP verwenden wollen)

**⚠️ Hinweis:** Die PHP-Version ist Legacy und wird nicht mehr aktiv entwickelt. Sie unterstützt NICHT:
- Agent-System
- LLM-Integration
- Automatische Stundenzettel-Verifikation
- Reisekosten-App mit Agents
- Urlaubsplaner mit Feiertags-Integration

**Falls Sie die PHP-Version trotzdem verwenden wollen:**

1. MySQL-Datenbank auf All-inkl erstellen (siehe `INSTALLATION_ALL_INKL.md`)
2. `webapp/` Ordner auf All-inkl hochladen
3. PHP-Konfiguration anpassen

**Empfehlung:** Verwenden Sie die aktuelle Python/FastAPI-Version auf Proxmox!

---

**Für Details zur Legacy PHP-Version siehe:** `INSTALLATION_ALL_INKL.md`

## Standard-Anmeldedaten

Nach der Installation:
- **E-Mail**: admin@schmitz-intralogistik.de
- **Passwort**: admin123

**⚠️ Wichtig:** Ändern Sie das Passwort sofort nach der ersten Anmeldung!

## Support

Bei Problemen:
1. Überprüfen Sie die PHP-Version (All-Inkl Kundenmenü → PHP-Einstellungen)
2. Kontrollieren Sie die Datenbankverbindung
3. Überprüfen Sie Dateiberechtigungen
4. Kontaktieren Sie bei Bedarf den All-Inkl Support

## Konfiguration für Reisekosten-App

### Lokaler Speicherpfad für Belege

Die Reisekosten-App speichert **alle PDF-Dateien** (Reisekosten-Belege und unterschriebene Stundenzettel) **nicht auf dem Webserver**, sondern auf einem lokalen Bürorechner in strukturierten Ordnern.

Konfigurieren Sie den Pfad in der `.env` Datei des Backends:

```env
LOCAL_RECEIPTS_PATH=C:/Reisekosten_Belege
```

**Wichtig:** 
- Dieser Pfad muss auf dem Rechner existieren, auf dem der Backend-Server läuft
- Der Server benötigt Schreibrechte auf diesem Verzeichnis
- Unter Windows: Verwenden Sie absolute Pfade mit Laufwerksbuchstaben (z.B. `C:/Reisekosten_Belege`)
- Unter Linux: Verwenden Sie absolute Pfade (z.B. `/var/receipts`)

### Ordner-Struktur für PDF-Dateien

**Alle vom User hochgeladenen PDF-Dateien werden in eindeutigen Ordnern gespeichert:**

#### Reisekosten-Belege
```
LOCAL_RECEIPTS_PATH/
└── reisekosten/
    └── User_Name_Monat_ReportID/
        ├── receipt_id_1_beleg.pdf
        ├── receipt_id_2_beleg.pdf
        └── ...
```

**Beispiel:**
- `Max_Mustermann_2025-01_abc123def456/`
  - `receipt_1_benzinkosten.pdf`
  - `receipt_2_hotel.pdf`
  - `receipt_3_parkplatz.pdf`

#### Unterschriebene Stundenzettel
```
LOCAL_RECEIPTS_PATH/
└── stundenzettel/
    └── User_Name_Woche_TimesheetID/
        └── timesheet_id_signed_20250101_120000_unterschrieben.pdf
```

**Beispiel:**
- `Max_Mustermann_2025-01-01_xyz789/`
  - `xyz789_signed_20250115_143000_stundenzettel_kunde.pdf`

**Vorteile:**
- ✅ Alle Belege einer Reisekosten-Abrechnung sind in einem Ordner
- ✅ Eindeutige Ordner-Namen (User_Monat_ReportID)
- ✅ Übersichtliche Struktur für Archivierung
- ✅ Beim Löschen einer Abrechnung wird der gesamte Ordner gelöscht

### Ollama LLM Integration

Für die automatische Prüfung von Reisekostenabrechnungen:

**Architektur:**
- Agents laufen auf Proxmox-Server
- LLMs laufen auf GMKTec evo x2 Rechner im lokalen Netzwerk

**Konfiguration:**
```env
OLLAMA_BASE_URL=http://192.168.1.100:11434  # IP des GMKTec-Servers
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=300
OLLAMA_MAX_RETRIES=3
```

Siehe **[backend/LLM_INTEGRATION.md](backend/LLM_INTEGRATION.md)** für Details.

## Push-Benachrichtigungen (PWA)

Die App unterstützt Web-Push. Wichtige Statusänderungen werden als Push gesendet, z.B.:
- User: Urlaub genehmigt
- Buchhaltung: neuer Beleg-Upload / unterschriebener Stundenzettel hochgeladen

### Backend (VAPID)

`.env` im Backend:
```env
VAPID_PUBLIC_KEY=YOUR_BASE64URL_PUBLIC_KEY
VAPID_PRIVATE_KEY=YOUR_BASE64URL_PRIVATE_KEY
VAPID_CLAIM_EMAIL=admin@ihre-domain.de
```

API:
- `GET /api/push/public-key` – liefert Public Key
- `POST /api/push/subscribe` – speichert Subscription des eingeloggten Users

### Frontend
- Service Worker registriert und abonniert Push nach Login
- Nutzer erteilen Browser-Berechtigung (Notification permission)

### Auslöser (Beispiele)
- Urlaub genehmigt → Push an User
- Beleg-Upload / unterschriebener Stundenzettel → Push an Rolle „accounting“

## 📚 Weitere Dokumentation

- **Installationsanleitungen:**
  - [INSTALLATION_ALL_INKL.md](INSTALLATION_ALL_INKL.md) - All-inkl.com spezifisch
  - [INSTALLATION_COMPLETE.md](INSTALLATION_COMPLETE.md) - Allgemeine Installation
  - [QUICK_START.md](QUICK_START.md) - Schnellstart

- **Feature-Dokumentation:**
  - [backend/AGENTS_README.md](backend/AGENTS_README.md) - Agent-Netzwerk
  - [backend/LLM_INTEGRATION.md](backend/LLM_INTEGRATION.md) - LLM-Integration (Proxmox/GMKTec)
  - [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Datenbank-Migration
  - [backend/MIGRATION_README.md](backend/MIGRATION_README.md) - Migration API
  - [backend/DSGVO_COMPLIANCE.md](backend/DSGVO_COMPLIANCE.md) - DSGVO & EU-AI-Act
  - [frontend/src/SECURITY.md](frontend/src/SECURITY.md) - Frontend-Sicherheit

- **Änderungshistorie:** Siehe [CHANGELOG.md](CHANGELOG.md)
