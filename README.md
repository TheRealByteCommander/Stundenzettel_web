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

Diese Anwendung ist für einen vollständig lokalen Betrieb auf Proxmox ausgelegt:

- ✅ **Frontend:** Eigener Proxmox-Container (z. B. Nginx + React Build)
- ✅ **Backend & MongoDB:** Zweiter Proxmox-Container (FastAPI, Agents, Datenbank, Dateispeicher)
- ✅ **Ollama (LLM):** GMKTec evo x2 im lokalen Netzwerk
- ✅ **Zugriff von außen:** DDNS + WireGuard VPN oder Reverse-Proxy auf dem Frontend-Container

### 📚 Installationsanleitungen

- **⭐ Primäre Anleitung:** **[INSTALLATION_COMPLETE_CORRECT.md](INSTALLATION_COMPLETE_CORRECT.md)** – Schritt-für-Schritt-Setup für zwei Proxmox-Container + GMKTec
- **Architektur-Details:** **[ARCHITEKTUR_ALL_INKL_PROXMOX.md](ARCHITEKTUR_ALL_INKL_PROXMOX.md)** – aktualisierte Übersicht der lokalen Container-Architektur
- **LLM-Integration:** **[backend/LLM_INTEGRATION.md](backend/LLM_INTEGRATION.md)** – Ollama-Setup auf dem GMKTec
- **Legacy PHP-Version:** **[INSTALLATION_ALL_INKL.md](INSTALLATION_ALL_INKL.md)** – nur für die nicht mehr empfohlene PHP-Variante
- **Windows-spezifisch:** **[WINDOWS_INSTALLATION.md](WINDOWS_INSTALLATION.md)**
- **Allgemeine Installation/Quickstart:** **[INSTALLATION_COMPLETE.md](INSTALLATION_COMPLETE.md)**, **[QUICK_START.md](QUICK_START.md)**
- **Frontend Dependency-Fixes:** **[frontend/INSTALLATION_FIX.md](frontend/INSTALLATION_FIX.md)**
- **Netzwerk-Routing/Tunnel:** **[OFFICE_RECHNER_ROUTING.md](OFFICE_RECHNER_ROUTING.md)**

### ⚙️ Vollautomatische Installation auf Proxmox-CTs

Für die Referenz-IPs `192.168.178.150` (Frontend), `192.168.178.151` (Backend) und `192.168.178.155` (GMKTec/Ollama) stehen zwei Skripte zur Verfügung. Die Skripte können direkt aus dem Repository geladen und gestartet werden; erforderliche Parameter werden über Umgebungsvariablen gesetzt.

**Backend-CT (FastAPI + MongoDB)**

```bash
curl -fsSL https://raw.githubusercontent.com/TheRealByteCommander/Stundenzettel_web/main/scripts/install_backend_ct.sh \
 | sudo DDNS_DOMAIN=my.ddns.example FRONTEND_IP=192.168.178.150 BACKEND_IP=192.168.178.151 OLLAMA_IP=192.168.178.155 bash
```

Optional lassen sich weitere Variablen wie `CORS_ORIGINS`, `SECRET_KEY`, `LOCAL_RECEIPTS_PATH` oder `REPO_BRANCH` mitgeben.

**Frontend-CT (Nginx + React Build)**

```bash
curl -fsSL https://raw.githubusercontent.com/TheRealByteCommander/Stundenzettel_web/main/scripts/install_frontend_ct.sh \
 | sudo DDNS_DOMAIN=my.ddns.example BACKEND_HOST=192.168.178.151 BACKEND_PORT=8000 bash
```

Sobald ein gültiges Zertifikat per Let’s Encrypt ausgestellt werden soll, den Aufruf ergänzen:

```bash
curl -fsSL https://raw.githubusercontent.com/TheRealByteCommander/Stundenzettel_web/main/scripts/install_frontend_ct.sh \
 | sudo DDNS_DOMAIN=my.ddns.example BACKEND_HOST=192.168.178.151 BACKEND_PORT=8000 \
   RUN_CERTBOT=true CERTBOT_EMAIL=admin@my.ddns.example bash
```

Die Skripte legen alle benötigten Pakete, Konfigurationen und systemd-Dienste automatisch an. Details und manuelle Alternativen sind in `INSTALLATION_PROXMOX_CT.md` beschrieben.

---

### ❌ Legacy PHP-Version (nur falls zwingend erforderlich)

**⚠️ Hinweis:** Die PHP-Version ist Legacy und wird nicht mehr aktiv entwickelt. Sie unterstützt NICHT:
- Agent-System
- LLM-Integration
- Automatische Stundenzettel-Verifikation
- Reisekosten-App mit Agents
- Urlaubsplaner mit Feiertags-Integration

**Falls Sie die PHP-Version trotzdem verwenden wollen:**

1. MySQL-Datenbank bereitstellen (siehe `INSTALLATION_ALL_INKL.md`)
2. `webapp/`-Ordner deployen
3. PHP-Konfiguration anpassen

**Empfehlung:** Verwenden Sie die aktuelle Proxmox-basierte Python/FastAPI-Version!

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
- LLMs laufen auf GMKTec evo x2 Rechner im lokalen Netzwerk (Referenz-IP `192.168.178.155`)

**Konfiguration:**
```env
OLLAMA_BASE_URL=http://192.168.178.155:11434  # IP des GMKTec-Servers
OLLAMA_MODEL=llama3.2
OLLAMA_MODEL_CHAT=llama3.2
OLLAMA_MODEL_DOCUMENT=mistral-nemo
OLLAMA_MODEL_ACCOUNTING=llama3.1
OLLAMA_TIMEOUT=300
OLLAMA_MAX_RETRIES=3
```
> Beispiel-IP-Plan: Frontend-CT `192.168.178.150`, Backend-CT `192.168.178.151`, GMKTec `192.168.178.155`. Passe die Werte bei eigenem Netz an.

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
