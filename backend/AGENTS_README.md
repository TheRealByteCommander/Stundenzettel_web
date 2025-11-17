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

**Tool-Registry**: Zentrale Verwaltung aller Tools (Singleton-Pattern)

## Abhängigkeiten

- `aiohttp`: Für Ollama API-Kommunikation und Web-Tools (mit Connection Pooling)
- `PyPDF2` oder `pdfplumber`: Für PDF-Text-Extraktion
- `pydantic`: Für Datenmodelle
- `cryptography`: Für DSGVO-konforme Verschlüsselung von PDFs
- `motor` (async MongoDB): Für Memory-Speicherung

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

