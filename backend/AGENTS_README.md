# Autogen Agent Network - Reisekostenabrechnung

## Übersicht

Dieses Modul implementiert ein Netzwerk von spezialisierten AI-Agenten zur automatischen Prüfung von Reisekostenabrechnungen mit Ollama LLMs.

## Agenten

### 1. Chat Agent (`ChatAgent`)
- **Aufgabe**: Dialog mit Benutzer, Rückfragen bei fehlenden Informationen
- **Features**:
  - Generiert klare Fragen zu fehlenden/unklaren Informationen
  - Verarbeitet Benutzer-Antworten
  - Entscheidet, ob weitere Informationen benötigt werden
  - **Memory-System**: Lernt aus früheren Konversationen und Benutzerpräferenzen
  - Speichert Dialoge und Erkenntnisse für bessere zukünftige Interaktionen

### 2. Dokumenten Agent (`DocumentAgent`)
- **Aufgabe**: Analyse von PDF-Belegen und Verifikation unterschriebener Stundenzettel
- **Features**:
  - **Text-Extraktion** aus PDFs (PyPDF2/pdfplumber)
  - **Automatische Verifikation unterschriebener Stundenzettel**:
    - Extrahiert PDF-Text (mit DSGVO-konformer Entschlüsselung)
    - Sucht nach Schlüsselwörtern für Unterschrift (z.B. "unterschrift", "signed", "signature")
    - Heuristische Prüfung des PDF-Inhalts
    - Speichert Verifikationsergebnis (`signed_pdf_verified`, `signed_pdf_verification_notes`)
    - **Automatische Genehmigung**: Wenn Unterschrift verifiziert wird, wird der Stundenzettel automatisch als "approved" markiert und die Arbeitszeit wird gutgeschrieben
    - **Buchhaltung genehmigt nur in Ausnahmefällen**: Wenn Agent Unterschrift nicht verifizieren kann, bleibt Status "sent" für manuelle Prüfung
  - **Dokumenttyp-Erkennung**: Hotel, Restaurant, Maut, Parken, Tanken, Bahnticket, etc.
  - **Sprache-Erkennung** und Übersetzung bei Bedarf
  - **Daten-Extraktion**: Betrag, Datum, Währung, Steuernummer, Firmenanschrift
  - **Vollständigkeitsprüfung**:
    - Steuernummer vorhanden?
    - Firmenanschrift vorhanden?
    - Betrag klar erkennbar?
    - Datum vorhanden?
  - **Validierung**: Identifiziert Probleme und Unstimmigkeiten
  - **Logik- und Machbarkeitsprüfung**:
    - **Überlappende Hotelrechnungen**: Erkennt, wenn mehrere Hotelrechnungen für denselben oder überlappende Zeiträume vorhanden sind
    - **Datum-Abgleich mit Arbeitsstunden**: Prüft, ob für das Dokument-Datum Arbeitsstunden im Stundenzettel verzeichnet sind
    - **Zeitliche Konsistenz**: Prüft, ob Rechnungsdatum und Leistungsdatum logisch sind
    - **Orts-Konsistenz**: Prüft, ob Dokument-Ort mit Reiseort übereinstimmt
    - **Betrags-Plausibilität**: Prüft, ob Beträge für den Dokumenttyp plausibel sind
  - **Automatische Zuordnung**: Ordnet Dokumente automatisch Reiseeinträgen zu (basierend auf Datum)
  - **Memory-System**: 
    - Speichert Analyseergebnisse und erkennt Muster
    - Lernt aus erfolgreichen Analysen für bessere Genauigkeit
    - Speichert typische Dokumentenmuster pro Kategorie

### 3. Buchhaltung Agent (`AccountingAgent`)
- **Aufgabe**: Zuordnung und Berechnung
- **Features**:
  - **Zuordnung**: Ordnet Dokumente Reiseeinträgen zu (basierend auf Datum, Ort, Zweck)
  - **Verpflegungsmehraufwand**: Automatische Berechnung basierend auf:
    - Land/Standort (aus Ortsangabe) - **mit Web-Geocoding**
    - Abwesenheitsdauer
    - **Aktuelle Spesensätze aus dem Internet** (Web-Suche für aktuelle Daten)
  - **Kategorisierung**: Hotel, Verpflegung, Transport (Maut/Parken/Tanken), etc.
  - **Zusätzliche Berechnung**: Verpflegungsmehraufwand für Reisetage ohne Belege
  - **Arbeitsstunden-Abgleich**: 
    - Jeder Reiseeintrag enthält `working_hours` (gutgeschriebene Arbeitsstunden aus Stundenzettel)
    - Prüft Reisekosten im Verhältnis zu den Arbeitsstunden auf Plausibilität
    - Stellt sicher, dass Reisekosten nur für Tage mit verifizierten und genehmigten Stundenzetteln abgerechnet werden
  - **Machbarkeitsprüfung und Logik-Validierung**:
    - **Überlappende Hotelrechnungen**: Erkennt und meldet, wenn mehrere Hotelrechnungen für denselben oder überlappende Zeiträume vorhanden sind
    - **Datum-Konsistenz**: Prüft, ob Dokument-Datum mit Reiseeintrag-Datum übereinstimmt
    - **Arbeitsstunden-Abgleich**: Prüft, ob für jeden Tag mit Reisekosten auch Arbeitsstunden im Stundenzettel verzeichnet sind
    - **Zeitliche Machbarkeit**: Prüft, ob Reisezeiten und Übernachtungen logisch sind (z.B. keine Übernachtung ohne Anreise)
    - **Orts-Konsistenz**: Prüft, ob Hotel-Ort mit Reiseort übereinstimmt
  - **Web-Tools Integration**:
    - **Geocoding-Tool**: Bestimmt Ländercode aus Ortsangabe (OpenStreetMap)
    - **Meal Allowance Lookup**: Sucht aktuelle Spesensätze im Internet
    - **Currency Exchange**: Rechnet Fremdwährungen in EUR um
  - **Memory-System**: 
    - Speichert Zuordnungsentscheidungen und lernt aus erfolgreichen Zuordnungen
    - Speichert gefundene Länder-Spesensätze für zukünftige Verwendung

### 4. Agent Orchestrator (`AgentOrchestrator`)
- **Aufgabe**: Orchestrierung des Agent-Netzwerks
- **Workflow**:
  1. Dokumenten Agent analysiert alle Belege
  2. Buchhaltung Agent ordnet zu und berechnet (nutzt Web-Tools für aktuelle Daten)
  3. Chat Agent stellt bei Bedarf Rückfragen
  4. Zusammenfassung wird generiert
- **Verwaltung**:
  - Initialisiert Memory-System für alle Agenten
  - Verwaltet Tool-Registry (Zugriff auf Web-Tools)
  - Koordiniert Kommunikation zwischen Agenten

## Konfiguration

### Ollama LLM Integration

**Für Proxmox Deployment:**
- Agents laufen auf Proxmox-Server
- LLMs laufen auf GMKTec evo x2 im lokalen Netzwerk

```env
# Netzwerk-Zugriff auf GMKTec evo x2
OLLAMA_BASE_URL=http://192.168.178.155:11434  # IP des GMKTec evo x2 Servers

# Agent-spezifische Modelle (aktuell konfiguriert)
OLLAMA_MODEL_CHAT=Qwen2.5:32B           # Hohe Qualität für Dialoge
OLLAMA_MODEL_DOCUMENT=Qwen2.5vl:7b      # Vision-Modell für Dokumente und Bilder
OLLAMA_MODEL_ACCOUNTING=DeepSeek-R1:32B # Reasoning-Modell für komplexe Logik

# Oder ein Modell für alle (einfacher, aber weniger optimiert)
OLLAMA_MODEL=llama3.2  # Fallback für alle Agents

# Timeout-Konfiguration
OLLAMA_TIMEOUT=300  # 5 Minuten (für große Modelle)
OLLAMA_MAX_RETRIES=3  # Retries bei Netzwerkfehlern
OLLAMA_RETRY_DELAY=2.0  # Sekunden zwischen Retries
```

**Features:**
- ✅ Agent-spezifische LLM-Konfiguration (jeder Agent bekommt optimales Modell)
- ✅ Connection Pooling für bessere Performance
- ✅ Automatische Retry-Logic bei Netzwerkfehlern
- ✅ Health Checks vor Verwendung
- ✅ Timeout-Konfiguration für große Modelle
- ✅ Detaillierte Fehlerbehandlung

**Siehe:**
- **[AGENT_LLM_CONFIG.md](AGENT_LLM_CONFIG.md)** für detaillierte LLM-Empfehlungen pro Agent
- **[LLM_INTEGRATION.md](LLM_INTEGRATION.md)** für vollständige Setup-Anleitung

### Spesensätze
Die Spesensätze werden in `MEAL_ALLOWANCE_RATES` gespeichert (Quelle: Bundesfinanzministerium) als Fallback.
**Der AccountingAgent nutzt jedoch automatisch Web-Tools**, um aktuelle Spesensätze aus dem Internet zu holen:

- **Automatische Web-Suche**: Sucht nach aktuellen Verpflegungsmehraufwand-Spesensätzen
- **Fallback**: Nutzt lokale Datenbank, wenn Web-Suche fehlschlägt
- **Alle Länder unterstützt**: Durch Geocoding-Tool können beliebige Länder erkannt werden

Aktuell in lokaler Datenbank hinterlegt:
- DE (Deutschland)
- AT (Österreich)
- CH (Schweiz)
- FR (Frankreich)
- IT (Italien)
- ES (Spanien)
- GB (Großbritannien)
- US (USA)

## Verwendung

### Automatische Prüfung starten
Wird automatisch ausgelöst, wenn eine Reisekostenabrechnung abgeschlossen wird:

```python
from agents import AgentOrchestrator

orchestrator = AgentOrchestrator()
# Prüft automatisch LLM-Verfügbarkeit
await orchestrator.ensure_llm_available()
result = await orchestrator.review_expense_report(report_id, db)
```

### Chat mit Agenten
```python
orchestrator = AgentOrchestrator()
await orchestrator.ensure_llm_available()
response = await orchestrator.handle_user_message(report_id, user_message, db)
```

### Health Check
```python
from agents import OllamaLLM

llm = OllamaLLM(base_url="http://192.168.178.155:11434")
is_healthy = await llm.health_check()
print(f"Ollama erreichbar: {is_healthy}")
```

## Agent Memory-System

Jeder Agent verfügt über ein **großes persistentes Gedächtnis** (bis zu 10.000 Einträge pro Agent):

- **Speicherung**: MongoDB Collection `agent_memory`
- **Eintragstypen**:
  - `conversation`: Gespeicherte Dialoge mit Benutzern
  - `analysis`: Dokumentenanalysen und Ergebnisse
  - `decision`: Getroffene Entscheidungen
  - `pattern`: Gelernte Muster (z.B. Dokumenttypen)
  - `insight`: Erkenntnisse und wichtige Informationen
  - `correction`: Korrekturen und Verbesserungen

- **Features**:
  - **Intelligente Suche**: Nach Text, Typ, Tags, Zeitraum
  - **Kontext-Generierung**: Relevante Informationen für LLM-Prompts
  - **Automatische Speicherung**: Alle wichtigen Aktionen werden gespeichert
  - **In-Memory Cache**: Schneller Zugriff auf die letzten 500 Einträge

**Memory wird automatisch in LLM-Prompts integriert**, sodass Agenten aus früheren Erfahrungen lernen.

## Agent Tools-System

Agenten haben Zugriff auf **Web-Tools** für aktuelle Daten:

### Verfügbare Tools

1. **WebSearchTool**
   - Web-Suche nach aktuellen Informationen
   - Nutzt DuckDuckGo (kein API-Key erforderlich)
   - Für Spesensätze, Regelungen, etc.

2. **CurrencyExchangeTool**
   - Aktuelle Wechselkurse zwischen Währungen
   - Nutzt exchangerate-api.com (kostenlos)
   - 1-Stunden-Cache für Performance
   - Für Reisekostenabrechnungen in Fremdwährung

3. **MealAllowanceLookupTool**
   - Sucht aktuelle Verpflegungsmehraufwand-Spesensätze
   - Kombiniert Web-Suche mit lokaler Datenbank
   - Automatische Extraktion von Beträgen

4. **GeocodingTool**
   - Bestimmt Ländercode aus Ortsangabe
   - Nutzt OpenStreetMap Nominatim API (kostenlos)
   - Fallback auf String-Erkennung
   - Für automatische Länderbestimmung

5. **OpenMapsTool** ⭐ NEU
   - Umfassendes Tool für OpenStreetMap-Funktionen
   - **Aktionen:**
     - `geocode`: Adresse zu Koordinaten (mit vollständigen Adressdetails)
     - `reverse`: Koordinaten zu Adresse (Reverse Geocoding)
     - `search`: POI-Suche (Hotels, Restaurants, Tankstellen, etc.) mit optionalem Radius
     - `distance`: Entfernungsberechnung zwischen zwei Koordinaten (Haversine-Formel)
     - `route`: Routenberechnung mit geschätzter Fahrzeit (Luftlinie)
   - Nutzt OpenStreetMap Nominatim API (kostenlos)
   - Nützlich für:
     - Ortsbestimmung und Validierung von Adressen in Reisekostenabrechnungen
     - POI-Suche (z.B. Hotels, Restaurants in der Nähe)
     - Entfernungsvalidierung zwischen Reisezielen
     - Standortinformationen für Dokumentenanalyse
   - **Verfügbar für alle Agents**: ChatAgent, DocumentAgent, AccountingAgent

**Tool-Registry**: Zentrale Verwaltung aller Tools (Singleton-Pattern)

**Wichtig**: Alle Agents (ChatAgent, DocumentAgent, AccountingAgent) haben jetzt Zugriff auf alle Tools, einschließlich des neuen OpenMapsTool.

6. **ExaSearchTool** ⭐ NEU (für ChatAgent)
   - Hochwertige semantische Suche mit Exa/XNG API
   - Besser als Standard-Web-Suche für präzise, relevante Ergebnisse
   - Nutzt Auto-Prompt für optimale Ergebnisse
   - **Erfordert**: `EXA_API_KEY` Umgebungsvariable und `pip install exa-py`
   - **Primär für**: ChatAgent zur Beantwortung von Fragen

7. **MarkerTool** ⭐ NEU (für DocumentAgent & AccountingAgent)
   - Erweiterte Dokumentenanalyse und -extraktion
   - Extrahiert strukturierte Daten aus PDFs und anderen Dokumenten
   - Unterstützt Tabellen- und Bild-Extraktion
   - Markdown-Output verfügbar
   - **Erfordert**: `MARKER_API_KEY` (optional) oder lokale Marker-Installation
   - **Primär für**: DocumentAgent und AccountingAgent

8. **PaddleOCRTool** ⭐ NEU (Fallback für DocumentAgent)
   - OCR-Tool für Texterkennung in Bildern und PDFs
   - Unterstützt über 100 Sprachen
   - Winkel-Klassifikation für bessere Ergebnisse
   - **Erfordert**: `pip install paddleocr paddlepaddle`
   - **Fallback für**: DocumentAgent wenn andere Methoden versagen

9. **CustomPythonRulesTool** ⭐ NEU (für AccountingAgent)
   - Führt benutzerdefinierte Python-Regeln für Buchhaltungsvalidierung aus
   - Vordefinierte Regeln: `validate_tax_number`, `check_receipt_completeness`, `calculate_meal_allowance`
   - Sichere Code-Ausführung mit eingeschränktem Kontext
   - Neue Regeln können zur Laufzeit registriert werden
   - **Primär für**: AccountingAgent zur Anwendung spezifischer Geschäftsregeln

10. **LangChainTool** ⭐ NEU (optional, für alle Agents)
    - LangChain-Integration für erweiterte Agent-Funktionalität
    - Ermöglicht komplexe Workflows, Tool-Orchestrierung
    - Erweiterte LLM-Interaktionen
    - **Erfordert**: `pip install langchain langchain-openai` (optional)
    - **Nützlich für**: Alle Agents, besonders für komplexe Entscheidungsprozesse
    - **Besonders empfohlen für**: AccountingAgent (komplexe Buchhaltungs-Workflows)

11. **WebAccessTool** ⭐ NEU (für alle Agents)
    - Generischer Web-Zugriff für HTTP-Requests zu beliebigen URLs
    - **Funktionen:**
      - GET/POST/PUT/DELETE/PATCH Requests
      - Web-Scraping (HTML-Inhalt extrahieren)
      - API-Zugriff (REST APIs)
      - JSON- und Form-Data-Unterstützung
      - HTML-Text-Extraktion
    - **Sicherheitsfeatures:**
      - URL-Validierung (nur HTTP/HTTPS)
      - Domain-Whitelist/Blacklist (konfigurierbar)
      - Blockierung privater IPs
      - Timeout-Kontrolle
    - **Konfiguration:**
      - `WEB_ACCESS_ALLOWED_DOMAINS`: Komma-getrennte Liste erlaubter Domains (optional, leer = alle erlaubt)
      - `WEB_ACCESS_BLOCKED_DOMAINS`: Komma-getrennte Liste blockierter Domains (Standard: localhost, 127.0.0.1)
    - **Nützlich für:**
      - **ChatAgent**: Aktuelle Informationen von spezifischen Websites abrufen
      - **DocumentAgent**: Dokumentenvalidierung über Web-APIs, Web-Scraping für Referenzdaten
      - **AccountingAgent**: Buchhaltungs-APIs, Steuer-Websites, Validierung über externe Services
    - **Verfügbar für alle Agents**: ChatAgent, DocumentAgent, AccountingAgent

12. **DateParserTool** ⭐ NEU (für alle Agents)
    - Datums-Parsing und -Validierung in verschiedenen Formaten
    - **Funktionen:**
      - Unterstützt internationale Datumsformate (DD.MM.YYYY, YYYY-MM-DD, DD/MM/YYYY, etc.)
      - Relative Daten (heute, gestern, morgen, vorgestern, übermorgen)
      - Datumsberechnungen (Wochentag, Wochenende-Erkennung)
      - Flexible Ausgabeformate (YYYY-MM-DD, DD.MM.YYYY, Timestamp, ISO)
    - **Nützlich für:**
      - **ChatAgent**: Datumsverständnis in Gesprächen
      - **DocumentAgent**: Datumsextraktion aus Dokumenten
      - **AccountingAgent**: Datumsvergleiche und Validierung
    - **Verfügbar für alle Agents**: ChatAgent, DocumentAgent, AccountingAgent

13. **TaxNumberValidatorTool** ⭐ NEU (für DocumentAgent und AccountingAgent)
    - Steuernummer-Validierung (USt-IdNr, VAT) für verschiedene Länder
    - **Unterstützte Länder:** DE, AT, CH, FR, IT, ES, GB, US
    - **Funktionen:**
      - Format-Validierung nach Ländercode
      - Normalisierung (entfernt Leerzeichen, Bindestriche)
      - Detaillierte Fehlermeldungen mit Format-Hinweisen
    - **Nützlich für:**
      - **DocumentAgent**: Beleg-Validierung
      - **AccountingAgent**: Steuernummer-Validierung bei Zuordnung
    - **Verfügbar für**: DocumentAgent, AccountingAgent

14. **TranslationTool** ⭐ NEU (für DocumentAgent)
    - Übersetzung zwischen Sprachen
    - **Funktionen:**
      - Unterstützt 100+ Sprachen
      - Automatische Spracherkennung (optional)
      - DeepL-API-Integration (falls `DEEPL_API_KEY` gesetzt)
    - **Konfiguration:**
      - `DEEPL_API_KEY`: DeepL API-Key für hochwertige Übersetzungen (optional)
    - **Nützlich für:**
      - **DocumentAgent**: Übersetzung mehrsprachiger Belege
    - **Verfügbar für**: DocumentAgent (primär)

15. **CurrencyValidatorTool** ⭐ NEU (für AccountingAgent)
    - Währungsvalidierung und -formatierung
    - **Funktionen:**
      - ISO 4217 Währungscode-Validierung
      - Betragsformatierung mit korrekten Dezimalstellen
      - Unterstützt 20+ Währungen (EUR, USD, GBP, CHF, JPY, etc.)
    - **Nützlich für:**
      - **AccountingAgent**: Währungsvalidierung und Betragsformatierung
    - **Verfügbar für**: AccountingAgent (primär)

16. **RegexPatternMatcherTool** ⭐ NEU (für alle Agents)
    - Mustererkennung in Texten mit regulären Ausdrücken
    - **Vordefinierte Patterns:**
      - `amount`: Beträge (123,45, € 123,45, $ 123.45)
      - `date`: Datumsangaben (15.01.2025, 2025-01-15)
      - `email`: E-Mail-Adressen
      - `tax_number`: Steuernummern (DE123456789, ATU12345678)
      - `phone`: Telefonnummern (international und national)
      - `iban`: IBAN-Nummern
      - `postal_code`: Postleitzahlen
    - **Funktionen:**
      - Eigene Regex-Patterns oder vordefinierte Patterns
      - Groß-/Kleinschreibung konfigurierbar
      - Finde alle Vorkommen oder nur das erste
    - **Nützlich für:**
      - **Alle Agents**: Datenextraktion und Mustererkennung
    - **Verfügbar für alle Agents**: ChatAgent, DocumentAgent, AccountingAgent

17. **PDFMetadataTool** ⭐ NEU (für DocumentAgent)
    - PDF-Metadaten-Extraktion
    - **Funktionen:**
      - Titel, Autor, Betreff
      - Erstellungs- und Änderungsdatum
      - Creator, Producer
      - Seitenzahl
      - Verschlüsselungsstatus
    - **Nützlich für:**
      - **DocumentAgent**: Dokumentenanalyse und Validierung
    - **Verfügbar für**: DocumentAgent (primär)

18. **DuplicateDetectionTool** ⭐ NEU PRIORITÄT 1 (für DocumentAgent und AccountingAgent)
    - Duplikats-Erkennung durch Hash-Vergleich
    - **Funktionen:**
      - SHA256-Hash-Berechnung für Dateien
      - Perceptual Hash für Bild-Ähnlichkeitsprüfung (optional, erfordert imagehash)
      - Datenbank-Abfrage nach bereits hochgeladenen Dateien
      - Automatische Warnung bei Duplikaten
    - **Erfordert**: Keine zusätzlichen Pakete (imagehash optional für Perceptual Hash)
    - **Nützlich für:**
      - **DocumentAgent**: Verhindert doppelte Beleg-Uploads
      - **AccountingAgent**: Prüft auf doppelte Abrechnungen
    - **Verfügbar für**: DocumentAgent, AccountingAgent

19. **IBANValidatorTool** ⭐ NEU PRIORITÄT 1 (für DocumentAgent und AccountingAgent)
    - IBAN-Validierung und Bankdaten-Extraktion
    - **Funktionen:**
      - Format-Validierung (ISO 13616)
      - Prüfziffern-Validierung (Modulo 97)
      - Länder-Erkennung aus IBAN
      - BBAN-Extraktion
      - BIC-Extraktion (vereinfacht, erfordert externe Datenbank)
    - **Unterstützte Länder:** 70+ Länder (DE, AT, CH, FR, IT, ES, GB, US, etc.)
    - **Nützlich für:**
      - **DocumentAgent**: Extrahiert und validiert IBANs aus Belegen
      - **AccountingAgent**: Validiert Überweisungsdaten
    - **Verfügbar für**: DocumentAgent, AccountingAgent

20. **ImageQualityTool** ⭐ NEU PRIORITÄT 1 (für DocumentAgent)
    - Qualitätsprüfung von gescannten Belegen
    - **Funktionen:**
      - DPI-Prüfung (Auflösung)
      - Schärfe-Analyse (Laplacian Variance)
      - Kontrast- und Helligkeitsprüfung
      - Automatische Verbesserungsvorschläge
      - OCR-Erfolgsrate-Vorhersage
    - **Erfordert**: `opencv-python`, `pillow` (bereits in requirements.txt)
    - **Nützlich für:**
      - **DocumentAgent**: Warnt vor schlechter Beleg-Qualität vor OCR
    - **Verfügbar für**: DocumentAgent (primär)

21. **TimeZoneTool** ⭐ NEU PRIORITÄT 1 (für AccountingAgent und ChatAgent)
    - Zeitzonen-Handling für internationale Reisen
    - **Funktionen:**
      - Zeitzonen-Erkennung aus Ortsangaben
      - UTC-Konvertierung
      - Zeitzonen-Offset-Berechnung
      - Reisezeit-Validierung (z.B. Ankunft vor Abreise bei Zeitzonen-Wechsel)
    - **Erfordert**: `pytz` (optional: `timezonefinder` für erweiterte Erkennung)
    - **Nützlich für:**
      - **AccountingAgent**: Validiert Reisezeiten bei internationalen Reisen
      - **ChatAgent**: Beantwortet Fragen zu Zeitzonen
    - **Verfügbar für**: AccountingAgent, ChatAgent

22. **EmailValidatorTool** ⭐ NEU PRIORITÄT 1 (für DocumentAgent und ChatAgent)
    - E-Mail-Validierung und Domain-Prüfung
    - **Funktionen:**
      - Format-Validierung (RFC 5322)
      - DNS MX-Record-Prüfung (Domain-Existenz)
      - Disposable-E-Mail-Erkennung
      - Längen-Validierung (RFC 5321)
    - **Erfordert**: `dnspython` (optional, für DNS-Prüfung)
    - **Nützlich für:**
      - **DocumentAgent**: Validiert E-Mail-Adressen in Belegen
      - **ChatAgent**: Validiert Benutzer-E-Mails
    - **Verfügbar für**: DocumentAgent, ChatAgent

23. **EmailParserTool** ⭐ NEU PRIORITÄT 2 (für DocumentAgent und AccountingAgent)
    - Automatische Beleg-Extraktion aus E-Mails
    - **Funktionen:**
      - IMAP/POP3-Zugriff auf E-Mail-Postfächer
      - Automatische Erkennung von Beleg-Anhängen (PDF, Bilder)
      - Extraktion von Betrag, Datum, Absender aus E-Mail-Text
      - Automatischer Upload in Reisekosten-Reports
    - **Erfordert**: `imapclient` (optional)
    - **Konfiguration**: E-Mail-Server, Benutzername, Passwort (über Parameter)
    - **Nützlich für:**
      - **DocumentAgent**: Automatische Beleg-Erkennung aus E-Mails
      - **AccountingAgent**: Automatische Zuordnung von E-Mail-Belegen
    - **Verfügbar für**: DocumentAgent, AccountingAgent

24. **SignatureDetectionTool** ⭐ NEU PRIORITÄT 2 (für DocumentAgent)
    - Erweiterte Signatur-Erkennung in PDFs
    - **Funktionen:**
      - Signatur-Feld-Erkennung (PDF-Signature Fields)
      - Digitale Signatur-Validierung (X.509-Zertifikate)
      - Handschriftliche Signatur-Erkennung (Text-Hinweise)
      - Signatur-Position-Analyse
    - **Erfordert**: PyPDF2 (bereits vorhanden)
    - **Nützlich für:**
      - **DocumentAgent**: Verbesserte Unterschriften-Verifikation für Stundenzettel
    - **Verfügbar für**: DocumentAgent (primär)

25. **ExcelImportExportTool** ⭐ NEU PRIORITÄT 2 (für AccountingAgent)
    - Excel/CSV-Import/Export für Buchhaltung
    - **Funktionen:**
      - Excel-Dateien lesen/schreiben (.xlsx, .xls)
      - CSV-Import/Export
      - Automatische Formatierung (Beträge, Datumsangaben)
      - Template-Generierung für Buchhaltung
    - **Erfordert**: `openpyxl` (optional, für Excel)
    - **Nützlich für:**
      - **AccountingAgent**: Exportiert Reisekosten-Reports für Buchhaltungssoftware
    - **Verfügbar für**: AccountingAgent (primär)

26. **PostalCodeValidatorTool** ⭐ NEU PRIORITÄT 2 (für DocumentAgent und AccountingAgent)
    - Postleitzahlen-Validierung und Adress-Verbesserung
    - **Funktionen:**
      - Postleitzahlen-Validierung (DE, AT, CH, FR, IT, ES, GB, US)
      - Adress-Normalisierung
      - Stadt-Erkennung aus PLZ (via OpenMaps)
      - Adress-Vervollständigung
    - **Nützlich für:**
      - **DocumentAgent**: Validiert Adressen in Belegen
      - **AccountingAgent**: Verbessert Adressdaten für Rechnungen
    - **Verfügbar für**: DocumentAgent, AccountingAgent

27. **PhoneNumberValidatorTool** ⭐ NEU PRIORITÄT 2 (für DocumentAgent)
    - Telefonnummer-Validierung und Formatierung
    - **Funktionen:**
      - Internationale Telefonnummer-Validierung (E.164)
      - Länder-Erkennung aus Telefonnummer
      - Formatierung (national/international/E.164)
      - Gültigkeitsprüfung
    - **Erfordert**: `phonenumbers` (optional)
    - **Nützlich für:**
      - **DocumentAgent**: Extrahiert und validiert Telefonnummern aus Belegen
    - **Verfügbar für**: DocumentAgent (primär)

28. **HolidayAPITool** ⭐ NEU PRIORITÄT 2 (für AccountingAgent)
    - Internationale Feiertags-Erkennung
    - **Funktionen:**
      - Feiertags-Erkennung für verschiedene Länder
      - Regionale Feiertage (z.B. sächsische Feiertage)
      - Feiertags-Kalender-Generierung
      - Einzelne Datums-Prüfung
    - **Erfordert**: `holidays` (bereits in requirements.txt)
    - **Nützlich für:**
      - **AccountingAgent**: Validiert Reisetage gegen Feiertage
    - **Verfügbar für**: AccountingAgent (primär)

29. **WeatherAPITool** ⭐ NEU PRIORITÄT 2 (für AccountingAgent)
    - Wetter-Daten für Reisevalidierung
    - **Funktionen:**
      - Wetter-API-Integration (OpenWeatherMap, WeatherAPI)
      - Aktuelle Wetterdaten
      - Temperatur, Feuchtigkeit, Windgeschwindigkeit
      - Reisezeit-Wetter-Validierung
    - **Erfordert**: `WEATHER_API_KEY` (OpenWeatherMap oder WeatherAPI)
    - **Konfiguration**: `WEATHER_API_KEY`, `WEATHER_API_PROVIDER` (openweathermap/weatherapi)
    - **Nützlich für:**
      - **AccountingAgent**: Validiert Reisezeiten gegen Wetterdaten
    - **Verfügbar für**: AccountingAgent (primär)

30. **TravelTimeCalculatorTool** ⭐ NEU PRIORITÄT 2 (für AccountingAgent)
    - Reisezeit-Berechnung zwischen Orten
    - **Funktionen:**
      - Google Maps API-Integration
      - OpenRouteService API-Integration (kostenlos)
      - Fahrtzeit-Berechnung (Auto, Bahn, Fahrrad, zu Fuß)
      - Distanz-Berechnung
      - Route-Optimierung
    - **Erfordert**: `GOOGLE_MAPS_API_KEY` oder `OPENROUTESERVICE_API_KEY`
    - **Konfiguration**: `GOOGLE_MAPS_API_KEY` oder `OPENROUTESERVICE_API_KEY`
    - **Nützlich für:**
      - **AccountingAgent**: Validiert Reisezeiten und -entfernungen
    - **Verfügbar für**: AccountingAgent (primär)

31. **PDFTimestampTool** ⭐ NEU PRIORITÄT 2 (für DocumentAgent)
    - Zeitstempel-Validierung in PDFs
    - **Funktionen:**
      - PDF-Erstellungsdatum-Extraktion
      - PDF-Änderungsdatum-Extraktion
      - Zeitstempel-Validierung (z.B. Beleg nicht nach Reisedatum erstellt)
      - Metadaten-Analyse
    - **Erfordert**: PyPDF2/pdfplumber (bereits vorhanden)
    - **Nützlich für:**
      - **DocumentAgent**: Validiert Beleg-Zeitstempel gegen Reisedaten
    - **Verfügbar für**: DocumentAgent (primär)

## Tool-Zuordnung zu Agents

### ChatAgent
- **Primär**: `exa_search` (Exa/XNG Suche)
- **Datumsverarbeitung**: `date_parser` (Datumsverständnis in Gesprächen)
- **Zeitzonen**: `timezone` (für Fragen zu internationalen Reisen)
- **E-Mail-Validierung**: `email_validator` (für E-Mail-Adressen-Validierung)
- **Mustererkennung**: `regex_pattern_matcher` (für Datenextraktion)
- **Web-Zugriff**: `web_access` (HTTP-Requests zu beliebigen URLs)
- **Optional**: `langchain`, `openmaps`, `web_search`, `currency_exchange`, `geocoding`

### DocumentAgent
- **Primär**: `marker` (Dokumentenanalyse)
- **Fallback**: `paddleocr` (OCR wenn andere Methoden versagen)
- **E-Mail-Parsing**: `email_parser` (automatische Beleg-Extraktion aus E-Mails)
- **Signatur-Erkennung**: `signature_detection` (erweiterte Signatur-Erkennung)
- **Duplikats-Prüfung**: `duplicate_detection` (verhindert doppelte Uploads)
- **Qualitätsprüfung**: `image_quality` (prüft Beleg-Qualität vor OCR)
- **PDF-Zeitstempel**: `pdf_timestamp` (validiert Erstellungsdatum gegen Reisedaten)
- **Übersetzung**: `translation` (für mehrsprachige Belege)
- **PDF-Metadaten**: `pdf_metadata` (Erstellungsdatum, Autor, etc.)
- **Validierung**: `tax_number_validator` (Steuernummer), `iban_validator` (IBAN), `email_validator` (E-Mail), `phone_number_validator` (Telefonnummer), `postal_code_validator` (Postleitzahl)
- **Datumsverarbeitung**: `date_parser` (Datumsextraktion aus Dokumenten)
- **Mustererkennung**: `regex_pattern_matcher` (für Datenextraktion)
- **Web-Zugriff**: `web_access` (für Validierung, API-Zugriff, Web-Scraping)
- **Optional**: `langchain`, `openmaps`, `web_search`

### AccountingAgent
- **Primär**: `marker` (Dokumentenanalyse), `custom_python_rules` (Buchhaltungsregeln)
- **Excel-Export**: `excel_import_export` (Excel/CSV-Import/Export für Buchhaltung)
- **E-Mail-Parsing**: `email_parser` (automatische Beleg-Extraktion aus E-Mails)
- **Duplikats-Prüfung**: `duplicate_detection` (verhindert doppelte Abrechnungen)
- **Validierung**: `tax_number_validator` (Steuernummer), `iban_validator` (IBAN), `currency_validator` (Währung), `postal_code_validator` (Postleitzahl)
- **Reisevalidierung**: `travel_time_calculator` (Reisezeit-Berechnung), `holiday_api` (Feiertags-Erkennung), `weather_api` (Wetter-Daten)
- **Zeitzonen**: `timezone` (für internationale Reisen, Reisezeit-Validierung)
- **Datumsverarbeitung**: `date_parser` (Datumsvergleiche und Validierung)
- **Mustererkennung**: `regex_pattern_matcher` (für Datenextraktion und Validierung)
- **Web-Zugriff**: `web_access` (für Buchhaltungs-APIs, Steuer-Websites, Validierung)
- **Optional**: `langchain` (besonders empfohlen für komplexe Workflows), `openmaps`, `geocoding`, `meal_allowance_lookup`, `currency_exchange`, `web_search`

## Abhängigkeiten

### Erforderlich
- `aiohttp`: Für Ollama API-Kommunikation und Web-Tools (mit Connection Pooling)
- `PyPDF2` oder `pdfplumber`: Für PDF-Text-Extraktion
- `pydantic`: Für Datenmodelle
- `cryptography`: Für DSGVO-konforme Verschlüsselung von PDFs
- `motor` (async MongoDB): Für Memory-Speicherung

### Optional (für erweiterte Tools)
- `exa-py`: Für ExaSearchTool (ChatAgent) - `pip install exa-py`
- `paddleocr` & `paddlepaddle`: Für PaddleOCRTool (DocumentAgent Fallback) - `pip install paddleocr paddlepaddle`
- `langchain` & `langchain-openai`: Für LangChainTool (alle Agents) - `pip install langchain langchain-openai`
- `imagehash`: Für DuplicateDetectionTool (Perceptual Hash) - `pip install imagehash`
- `opencv-python`: Für ImageQualityTool - `pip install opencv-python`
- `pytz`: Für TimeZoneTool - `pip install pytz`
- `timezonefinder`: Für TimeZoneTool (erweiterte Zeitzonen-Erkennung) - `pip install timezonefinder`
- `dnspython`: Für EmailValidatorTool (DNS MX-Record-Prüfung) - `pip install dnspython`
- `imapclient`: Für EmailParserTool (E-Mail-Parsing) - `pip install imapclient`
- `openpyxl`: Für ExcelImportExportTool (Excel-Dateien) - `pip install openpyxl`
- `phonenumbers`: Für PhoneNumberValidatorTool (Telefonnummer-Validierung) - `pip install phonenumbers`
- `holidays`: Für HolidayAPITool (Feiertags-Erkennung, bereits in requirements.txt)
- Marker: Lokale Installation oder API-Key für MarkerTool

### Umgebungsvariablen (optional)
- `EXA_API_KEY`: Für ExaSearchTool
- `MARKER_API_KEY`: Für MarkerTool (wenn API verwendet wird)
- `MARKER_BASE_URL`: Für MarkerTool API (Standard: `https://api.marker.io/v1`)
- `DEEPL_API_KEY`: Für TranslationTool (DeepL-API für hochwertige Übersetzungen)
- `WEATHER_API_KEY`: Für WeatherAPITool (OpenWeatherMap oder WeatherAPI)
- `WEATHER_API_PROVIDER`: Für WeatherAPITool (Standard: `openweathermap`, alternativ: `weatherapi`)
- `GOOGLE_MAPS_API_KEY`: Für TravelTimeCalculatorTool (Google Maps API, optional)
- `OPENROUTESERVICE_API_KEY`: Für TravelTimeCalculatorTool (OpenRouteService API, kostenlos, empfohlen)
- `WEB_ACCESS_ALLOWED_DOMAINS`: Komma-getrennte Liste erlaubter Domains für WebAccessTool (optional, leer = alle erlaubt)
- `WEB_ACCESS_BLOCKED_DOMAINS`: Komma-getrennte Liste blockierter Domains für WebAccessTool (Standard: `localhost,127.0.0.1,0.0.0.0`)

## DSGVO & EU-AI-Act Compliance

- ✅ **Datenverschlüsselung**: PDFs werden verschlüsselt gespeichert
- ✅ **Audit-Logging**: Alle AI-Entscheidungen werden geloggt
- ✅ **AI-Transparenz**: EU-AI-Act Art. 13 konform
- ✅ **Retention-Management**: Automatische Löschung abgelaufener Daten

Siehe **[DSGVO_COMPLIANCE.md](DSGVO_COMPLIANCE.md)** für Details.

## Erweiterte Features

✅ **Bereits implementiert:**
- ✅ Persistentes Memory-System für alle Agenten (10.000 Einträge pro Agent)
- ✅ Web-Tool-System mit aktuellem Datenzugriff
- ✅ Geocoding API für exakte Länderbestimmung
- ✅ Web-Suche für aktuelle Spesensätze
- ✅ Währungswechselkurs-API

**Zukünftig geplant:**
- OCR für gescannte Dokumente
- Bildanalyse für Foto-Belege
- Automatische Übersetzung bei fremdsprachigen Dokumenten
- Echtheitsprüfung mit ML-Modellen
- Erweiterte Tool-Integration (z.B. Steuernummer-Validierung)

