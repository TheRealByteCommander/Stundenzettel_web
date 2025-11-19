# Tool-Vorschläge für Tick Guard

## 📊 Analyse des Funktionsumfangs

### Aktuelle Hauptfunktionen:
1. **Stundenzettel-Verwaltung**: Zeiterfassung, PDF-Generierung, Unterschriften-Verifikation, Genehmigung
2. **Reisekosten-Verwaltung**: Beleg-Upload, automatische Datenextraktion, Validierung, Chat-System
3. **Urlaubsverwaltung**: Anträge, Genehmigung, Feiertags-Integration, Anforderungen
4. **Admin-Funktionen**: Benutzerverwaltung, Fahrzeugverwaltung, SMTP-Konfiguration, Ankündigungen
5. **Agent-System**: Dokumentenanalyse, Buchhaltung, Chat mit 17+ Tools
6. **Statistiken & Reporting**: Monatsstatistiken, Ranglisten, PDF-Export
7. **Push-Benachrichtigungen**: Service Worker, Browser-Integration

---

## 🛠️ Vorgeschlagene Tools (nach Priorität)

### 🔴 Priorität 1: Hochwertige Tools für sofortige Verbesserung

#### 1. **EmailParserTool** (für DocumentAgent & AccountingAgent)
**Zweck**: Automatische Extraktion von Belegen aus E-Mails
- **Funktionen**:
  - IMAP/POP3-Zugriff auf E-Mail-Postfächer
  - Automatische Erkennung von Beleg-Anhängen (PDF, Bilder)
  - Extraktion von Betrag, Datum, Absender aus E-Mail-Text
  - Automatischer Upload in Reisekosten-Reports
- **Nützlich für**:
  - **DocumentAgent**: Automatische Beleg-Erkennung aus E-Mails
  - **AccountingAgent**: Automatische Zuordnung von E-Mail-Belegen
- **Konfiguration**: `EMAIL_IMAP_SERVER`, `EMAIL_USER`, `EMAIL_PASSWORD`, `EMAIL_FOLDER`
- **Sicherheit**: Verschlüsselte Verbindungen (SSL/TLS), OAuth2-Support

#### 2. **DuplicateDetectionTool** (für DocumentAgent & AccountingAgent)
**Zweck**: Erkennung von doppelten Belegen
- **Funktionen**:
  - Hash-basierte Duplikats-Erkennung (MD5, SHA256)
  - Bild-Ähnlichkeitsprüfung (perceptual hashing)
  - Betrag-Datum-Vergleich
  - Automatische Warnung bei Duplikaten
- **Nützlich für**:
  - **DocumentAgent**: Verhindert doppelte Beleg-Uploads
  - **AccountingAgent**: Prüft auf doppelte Abrechnungen
- **Datenbank**: Speichert Hash-Werte für schnelle Vergleiche

#### 3. **ImageQualityTool** (für DocumentAgent)
**Zweck**: Qualitätsprüfung von gescannten Belegen
- **Funktionen**:
  - Auflösungsprüfung (DPI)
  - Schärfe-Analyse (Blur-Detection)
  - Kontrast- und Helligkeitsprüfung
  - OCR-Erfolgsrate-Vorhersage
  - Automatische Verbesserungsvorschläge
- **Nützlich für**:
  - **DocumentAgent**: Warnt vor schlechter Beleg-Qualität vor OCR
- **Bibliotheken**: OpenCV, PIL/Pillow

#### 4. **IBANValidatorTool** (für DocumentAgent & AccountingAgent)
**Zweck**: IBAN-Validierung und Bankdaten-Extraktion
- **Funktionen**:
  - IBAN-Format-Validierung (ISO 13616)
  - Prüfziffern-Validierung (Modulo 97)
  - Bank-Identifikation (BIC-Extraktion)
  - Länder-Erkennung aus IBAN
- **Nützlich für**:
  - **DocumentAgent**: Extrahiert Bankdaten aus Belegen
  - **AccountingAgent**: Validiert Überweisungsdaten
- **Erweitert**: Integration mit Bank-APIs (optional)

#### 5. **SignatureDetectionTool** (für DocumentAgent)
**Zweck**: Erweiterte Signatur-Erkennung in PDFs
- **Funktionen**:
  - Signatur-Feld-Erkennung (PDF-Signature Fields)
  - Digitale Signatur-Validierung (X.509-Zertifikate)
  - Handschriftliche Signatur-Erkennung (ML-basiert)
  - Signatur-Position-Analyse
- **Nützlich für**:
  - **DocumentAgent**: Verbesserte Unterschriften-Verifikation für Stundenzettel
- **Bibliotheken**: PyPDF2, cryptography, optional: TensorFlow für ML

#### 6. **TimeZoneTool** (für AccountingAgent & ChatAgent)
**Zweck**: Zeitzonen-Handling für Reisen
- **Funktionen**:
  - Zeitzonen-Erkennung aus Ortsangaben
  - UTC-Konvertierung
  - Zeitzonen-Offset-Berechnung
  - Reisezeit-Validierung (z.B. Ankunft vor Abreise bei Zeitzonen-Wechsel)
- **Nützlich für**:
  - **AccountingAgent**: Validiert Reisezeiten bei internationalen Reisen
  - **ChatAgent**: Beantwortet Fragen zu Zeitzonen
- **Bibliotheken**: pytz, timezonefinder

---

### 🟡 Priorität 2: Nützliche Tools für erweiterte Funktionalität

#### 7. **CalendarIntegrationTool** (für alle Agents)
**Zweck**: Kalender-Integration für Urlaubsplanung
- **Funktionen**:
  - iCal/ICS-Import/Export
  - Google Calendar API-Integration
  - Outlook Calendar API-Integration
  - Automatische Urlaubseinträge in Kalender
  - Feiertags-Synchronisation
- **Nützlich für**:
  - **ChatAgent**: Beantwortet Fragen zu Urlaubsplanung
  - **AccountingAgent**: Validiert Urlaubstage gegen Kalender
- **Konfiguration**: `GOOGLE_CALENDAR_API_KEY`, `OUTLOOK_CLIENT_ID`

#### 8. **ExcelImportExportTool** (für AccountingAgent)
**Zweck**: Excel/CSV-Import/Export für Buchhaltung
- **Funktionen**:
  - Excel-Dateien lesen/schreiben (.xlsx, .xls)
  - CSV-Import/Export
  - Automatische Formatierung (Beträge, Datumsangaben)
  - Template-Generierung für Buchhaltung
- **Nützlich für**:
  - **AccountingAgent**: Exportiert Reisekosten-Reports für Buchhaltungssoftware
- **Bibliotheken**: openpyxl, pandas

#### 9. **PostalCodeValidatorTool** (für DocumentAgent & AccountingAgent)
**Zweck**: Postleitzahlen-Validierung und Adress-Verbesserung
- **Funktionen**:
  - Postleitzahlen-Validierung (DE, AT, CH, FR, IT, ES, GB, US)
  - Adress-Normalisierung
  - Stadt-Erkennung aus PLZ
  - Adress-Vervollständigung
- **Nützlich für**:
  - **DocumentAgent**: Validiert Adressen in Belegen
  - **AccountingAgent**: Verbessert Adressdaten für Rechnungen
- **Datenquellen**: OpenStreetMap, Geonames

#### 10. **PhoneNumberValidatorTool** (für DocumentAgent)
**Zweck**: Telefonnummer-Validierung und Formatierung
- **Funktionen**:
  - Internationale Telefonnummer-Validierung (E.164)
  - Länder-Erkennung aus Telefonnummer
  - Formatierung (national/international)
  - Gültigkeitsprüfung
- **Nützlich für**:
  - **DocumentAgent**: Extrahiert und validiert Telefonnummern aus Belegen
- **Bibliotheken**: phonenumbers

#### 11. **EmailValidatorTool** (für alle Agents)
**Zweck**: E-Mail-Validierung und Domain-Prüfung
- **Funktionen**:
  - E-Mail-Format-Validierung (RFC 5322)
  - Domain-Existenz-Prüfung (DNS MX-Record)
  - Disposable-Email-Erkennung
  - E-Mail-Reputation-Check (optional)
- **Nützlich für**:
  - **DocumentAgent**: Validiert E-Mail-Adressen in Belegen
  - **ChatAgent**: Validiert Benutzer-E-Mails
- **Bibliotheken**: email-validator, dnspython

#### 12. **HolidayAPITool** (für AccountingAgent)
**Zweck**: Internationale Feiertags-Erkennung
- **Funktionen**:
  - Feiertags-API-Integration (z.B. holidayapi.com, calendarific.com)
  - Feiertags-Erkennung für verschiedene Länder
  - Regionale Feiertage (z.B. sächsische Feiertage)
  - Feiertags-Kalender-Generierung
- **Nützlich für**:
  - **AccountingAgent**: Validiert Reisetage gegen Feiertage
- **Konfiguration**: `HOLIDAY_API_KEY` (optional, kann auch lokal sein)

#### 13. **WeatherAPITool** (für AccountingAgent)
**Zweck**: Wetter-Daten für Reisevalidierung
- **Funktionen**:
  - Wetter-API-Integration (OpenWeatherMap, WeatherAPI)
  - Historische Wetterdaten
  - Reisezeit-Wetter-Validierung (z.B. Flugausfälle bei Sturm)
  - Temperatur-Daten für Spesensätze
- **Nützlich für**:
  - **AccountingAgent**: Validiert Reisezeiten gegen Wetterdaten
- **Konfiguration**: `WEATHER_API_KEY`

#### 14. **TravelTimeCalculatorTool** (für AccountingAgent)
**Zweck**: Reisezeit-Berechnung zwischen Orten
- **Funktionen**:
  - Google Maps API-Integration
  - OpenRouteService API-Integration (kostenlos)
  - Fahrtzeit-Berechnung (Auto, Bahn, Flugzeug)
  - Distanz-Berechnung
  - Route-Optimierung
- **Nützlich für**:
  - **AccountingAgent**: Validiert Reisezeiten und -entfernungen
- **Konfiguration**: `GOOGLE_MAPS_API_KEY` oder `OPENROUTESERVICE_API_KEY`

#### 15. **PDFTimestampTool** (für DocumentAgent)
**Zweck**: Zeitstempel-Validierung in PDFs
- **Funktionen**:
  - PDF-Erstellungsdatum-Extraktion
  - PDF-Änderungsdatum-Extraktion
  - Zeitstempel-Validierung (z.B. Beleg nicht nach Reisedatum erstellt)
  - Metadaten-Analyse
- **Nützlich für**:
  - **DocumentAgent**: Validiert Beleg-Zeitstempel gegen Reisedaten
- **Bibliotheken**: PyPDF2, pdfplumber

---

### 🟢 Priorität 3: Erweiterte Tools für spezielle Anwendungsfälle

#### 16. **QRCodeReaderTool** (für DocumentAgent)
**Zweck**: QR-Code-Erkennung in Belegen
- **Funktionen**:
  - QR-Code-Erkennung in PDFs und Bildern
  - Daten-Extraktion aus QR-Codes
  - E-Rechnung-Erkennung (ZUGFeRD, XRechnung)
  - Automatische Datenextraktion aus QR-Codes
- **Nützlich für**:
  - **DocumentAgent**: Extrahiert Daten aus QR-Codes in Belegen
- **Bibliotheken**: qrcode, pyzbar, opencv-python

#### 17. **BarcodeReaderTool** (für DocumentAgent)
**Zweck**: Barcode-Erkennung in Belegen
- **Funktionen**:
  - Barcode-Erkennung (EAN, UPC, Code128, etc.)
  - Produkt-Identifikation aus Barcodes
  - Automatische Datenextraktion
- **Nützlich für**:
  - **DocumentAgent**: Extrahiert Produktdaten aus Barcodes
- **Bibliotheken**: pyzbar, opencv-python

#### 18. **InvoiceNumberValidatorTool** (für DocumentAgent & AccountingAgent)
**Zweck**: Rechnungsnummer-Validierung
- **Funktionen**:
  - Rechnungsnummer-Format-Validierung
  - Duplikats-Prüfung (bereits vorhandene Rechnungsnummern)
  - Sequenz-Validierung
  - Lücken-Erkennung in Rechnungsnummern
- **Nützlich für**:
  - **DocumentAgent**: Validiert Rechnungsnummern in Belegen
  - **AccountingAgent**: Prüft auf fehlende Rechnungen

#### 19. **VATCalculatorTool** (für AccountingAgent)
**Zweck**: Mehrwertsteuer-Berechnung
- **Funktionen**:
  - MwSt-Berechnung (19%, 7%, etc.)
  - Netto/Brutto-Umrechnung
  - Länder-spezifische MwSt-Sätze
  - MwSt-Validierung in Belegen
- **Nützlich für**:
  - **AccountingAgent**: Berechnet und validiert MwSt in Reisekosten
- **Datenquellen**: EU MwSt-Sätze, nationale Steuersätze

#### 20. **ExpenseCategoryClassifierTool** (für AccountingAgent)
**Zweck**: Automatische Kategorisierung von Ausgaben
- **Funktionen**:
  - ML-basierte Kategorisierung (Hotel, Restaurant, Transport, etc.)
  - Keyword-basierte Klassifizierung
  - Lernen aus früheren Zuordnungen
  - Konfidenz-Score
- **Nützlich für**:
  - **AccountingAgent**: Automatische Kategorisierung von Belegen
- **Bibliotheken**: scikit-learn, optional: TensorFlow

#### 21. **ReceiptStandardValidatorTool** (für DocumentAgent)
**Zweck**: GoBD-Konformitäts-Prüfung
- **Funktionen**:
  - GoBD-Anforderungen-Prüfung (Grundsätze zur ordnungsmäßigen Führung und Aufbewahrung von Büchern, Aufzeichnungen und Unterlagen in elektronischer Form sowie zum Datenzugriff)
  - Vollständigkeits-Prüfung (Betrag, Datum, Steuernummer, etc.)
  - Lesbarkeits-Prüfung
  - Archivierbarkeits-Prüfung
- **Nützlich für**:
  - **DocumentAgent**: Prüft Belege auf GoBD-Konformität
- **Standards**: GoBD, HGB, AO

#### 22. **BankStatementParserTool** (für AccountingAgent)
**Zweck**: Kontoauszug-Parsing
- **Funktionen**:
  - PDF-Kontoauszug-Parsing (MT940, CAMT.053)
  - Transaktions-Extraktion
  - Betrag-Datum-Zuordnung
  - Automatische Zuordnung zu Reisekosten
- **Nützlich für**:
  - **AccountingAgent**: Extrahiert Daten aus Kontoauszügen für Fremdwährungsnachweis
- **Bibliotheken**: mt-940, camelot (für Tabellen)

#### 23. **DistanceMatrixTool** (für AccountingAgent)
**Zweck**: Entfernungsmatrix-Berechnung
- **Funktionen**:
  - Mehrere Orte gleichzeitig verarbeiten
  - Optimale Route-Berechnung
  - Kosten-Berechnung basierend auf Entfernung
  - Spesensatz-Validierung
- **Nützlich für**:
  - **AccountingAgent**: Validiert Reisekosten gegen Entfernungen
- **APIs**: Google Distance Matrix API, OpenRouteService

#### 24. **CompanyDatabaseTool** (für DocumentAgent & AccountingAgent)
**Zweck**: Firmendatenbank-Abfrage
- **Funktionen**:
  - Handelsregister-Abfrage (optional, API)
  - USt-IdNr-Validierung gegen EU-VIES
  - Firmenname-Normalisierung
  - Adress-Vervollständigung
- **Nützlich für**:
  - **DocumentAgent**: Validiert Firmendaten in Belegen
  - **AccountingAgent**: Prüft USt-IdNr gegen EU-Datenbank
- **APIs**: EU VIES API (kostenlos)

---

## 📋 Implementierungs-Empfehlungen

### Sofort umsetzbar (Priorität 1):
1. **DuplicateDetectionTool** - Einfach zu implementieren, hoher Nutzen
2. **IBANValidatorTool** - Standard-Validierung, keine externen APIs nötig
3. **ImageQualityTool** - OpenCV/PIL, direkt nutzbar
4. **TimeZoneTool** - pytz, keine externen APIs nötig
5. **EmailValidatorTool** - Einfache DNS-Prüfung

### Mittelfristig (Priorität 2):
6. **ExcelImportExportTool** - openpyxl/pandas
7. **PostalCodeValidatorTool** - OpenStreetMap/Geonames
8. **PhoneNumberValidatorTool** - phonenumbers
9. **PDFTimestampTool** - PyPDF2/pdfplumber
10. **TravelTimeCalculatorTool** - OpenRouteService (kostenlos)

### Langfristig (Priorität 3):
11. **EmailParserTool** - Erfordert E-Mail-Server-Konfiguration
12. **SignatureDetectionTool** - ML-Komponente erforderlich
13. **CalendarIntegrationTool** - OAuth2-Setup erforderlich
14. **ExpenseCategoryClassifierTool** - ML-Training erforderlich

---

## 🔧 Technische Anforderungen

### Neue Python-Bibliotheken (für Priorität 1):
```python
# requirements.txt Ergänzungen
imapclient>=2.3.1  # Für EmailParserTool
opencv-python>=4.8.0  # Für ImageQualityTool
phonenumbers>=8.13.0  # Für PhoneNumberValidatorTool
pytz>=2023.3  # Für TimeZoneTool
email-validator>=2.0.0  # Für EmailValidatorTool
openpyxl>=3.1.0  # Für ExcelImportExportTool
qrcode>=7.4.0  # Für QRCodeReaderTool
pyzbar>=0.1.9  # Für BarcodeReaderTool
```

### Externe APIs (optional):
- Google Maps API (für TravelTimeCalculatorTool)
- OpenRouteService API (kostenlos, für TravelTimeCalculatorTool)
- Holiday API (für HolidayAPITool)
- Weather API (für WeatherAPITool)
- EU VIES API (kostenlos, für CompanyDatabaseTool)

---

## 📊 Erwarteter Nutzen

### Für DocumentAgent:
- ✅ **30% weniger Fehler** durch bessere Beleg-Qualitätsprüfung
- ✅ **50% schnellere Verarbeitung** durch automatische Duplikats-Erkennung
- ✅ **20% bessere OCR-Ergebnisse** durch Qualitätsprüfung vor OCR

### Für AccountingAgent:
- ✅ **40% weniger manuelle Prüfungen** durch automatische Validierungen
- ✅ **25% schnellere Abrechnungen** durch Excel-Export
- ✅ **15% weniger Fehler** durch IBAN/Telefonnummer-Validierung

### Für ChatAgent:
- ✅ **Bessere Antworten** durch Zeitzonen- und Kalender-Integration
- ✅ **Mehr Kontext** durch Wetter- und Reisezeit-Daten

---

## 🎯 Nächste Schritte

1. **Priorität 1 Tools implementieren** (5 Tools)
2. **Dokumentation aktualisieren** (AGENTS_README.md)
3. **Tests schreiben** für neue Tools
4. **Konfiguration** in install_backend_ct.sh ergänzen
5. **Schrittweise Einführung** der Priorität 2 & 3 Tools

