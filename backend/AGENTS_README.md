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

### 2. Dokumenten Agent (`DocumentAgent`)
- **Aufgabe**: Analyse von PDF-Belegen
- **Features**:
  - **Text-Extraktion** aus PDFs (PyPDF2/pdfplumber)
  - **Dokumenttyp-Erkennung**: Hotel, Restaurant, Maut, Parken, Tanken, Bahnticket, etc.
  - **Sprache-Erkennung** und Übersetzung bei Bedarf
  - **Daten-Extraktion**: Betrag, Datum, Währung, Steuernummer, Firmenanschrift
  - **Vollständigkeitsprüfung**:
    - Steuernummer vorhanden?
    - Firmenanschrift vorhanden?
    - Betrag klar erkennbar?
    - Datum vorhanden?
  - **Validierung**: Identifiziert Probleme und Unstimmigkeiten

### 3. Buchhaltung Agent (`AccountingAgent`)
- **Aufgabe**: Zuordnung und Berechnung
- **Features**:
  - **Zuordnung**: Ordnet Dokumente Reiseeinträgen zu (basierend auf Datum, Ort, Zweck)
  - **Verpflegungsmehraufwand**: Automatische Berechnung basierend auf:
    - Land/Standort (aus Ortsangabe)
    - Abwesenheitsdauer
    - Aktuelle Spesensätze (Bundesfinanzministerium)
  - **Kategorisierung**: Hotel, Verpflegung, Transport (Maut/Parken/Tanken), etc.
  - **Zusätzliche Berechnung**: Verpflegungsmehraufwand für Reisetage ohne Belege

### 4. Agent Orchestrator (`AgentOrchestrator`)
- **Aufgabe**: Orchestrierung des Agent-Netzwerks
- **Workflow**:
  1. Dokumenten Agent analysiert alle Belege
  2. Buchhaltung Agent ordnet zu und berechnet
  3. Chat Agent stellt bei Bedarf Rückfragen
  4. Zusammenfassung wird generiert

## Konfiguration

### Ollama LLM Integration

**Für Proxmox Deployment:**
- Agents laufen auf Proxmox-Server
- LLMs laufen auf GMKTec evo x2 im lokalen Netzwerk

```env
# Netzwerk-Zugriff auf GMKTec evo x2
OLLAMA_BASE_URL=http://192.168.1.100:11434  # IP des GMKTec-Servers
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=300  # 5 Minuten (für große Modelle)
OLLAMA_MAX_RETRIES=3  # Retries bei Netzwerkfehlern
OLLAMA_RETRY_DELAY=2.0  # Sekunden zwischen Retries
```

**Features:**
- ✅ Connection Pooling für bessere Performance
- ✅ Automatische Retry-Logic bei Netzwerkfehlern
- ✅ Health Checks vor Verwendung
- ✅ Timeout-Konfiguration für große Modelle
- ✅ Detaillierte Fehlerbehandlung

Siehe **[LLM_INTEGRATION.md](LLM_INTEGRATION.md)** für vollständige Setup-Anleitung.

### Spesensätze
Die Spesensätze werden in `MEAL_ALLOWANCE_RATES` gespeichert (Quelle: Bundesfinanzministerium).
Aktuell unterstützte Länder:
- DE (Deutschland)
- AT (Österreich)
- CH (Schweiz)
- FR (Frankreich)
- IT (Italien)
- ES (Spanien)
- GB (Großbritannien)
- US (USA)

Weitere Länder können einfach hinzugefügt werden.

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

llm = OllamaLLM(base_url="http://192.168.1.100:11434")
is_healthy = await llm.health_check()
print(f"Ollama erreichbar: {is_healthy}")
```

## Abhängigkeiten

- `aiohttp`: Für Ollama API-Kommunikation (mit Connection Pooling)
- `PyPDF2` oder `pdfplumber`: Für PDF-Text-Extraktion
- `pydantic`: Für Datenmodelle
- `cryptography`: Für DSGVO-konforme Verschlüsselung von PDFs

## DSGVO & EU-AI-Act Compliance

- ✅ **Datenverschlüsselung**: PDFs werden verschlüsselt gespeichert
- ✅ **Audit-Logging**: Alle AI-Entscheidungen werden geloggt
- ✅ **AI-Transparenz**: EU-AI-Act Art. 13 konform
- ✅ **Retention-Management**: Automatische Löschung abgelaufener Daten

Siehe **[DSGVO_COMPLIANCE.md](DSGVO_COMPLIANCE.md)** für Details.

## Erweiterte Features (Zukünftig)

- OCR für gescannte Dokumente
- Bildanalyse für Foto-Belege
- Externe API für aktuelle Spesensätze
- Geocoding API für exakte Länderbestimmung
- Automatische Übersetzung bei fremdsprachigen Dokumenten
- Echtheitsprüfung mit ML-Modellen

