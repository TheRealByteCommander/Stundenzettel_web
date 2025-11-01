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

### Ollama
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

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
result = await orchestrator.review_expense_report(report_id, db)
```

### Chat mit Agenten
```python
response = await orchestrator.handle_user_message(report_id, user_message, db)
```

## Abhängigkeiten

- `aiohttp`: Für Ollama API-Kommunikation
- `PyPDF2` oder `pdfplumber`: Für PDF-Text-Extraktion
- `pydantic`: Für Datenmodelle

## Erweiterte Features (Zukünftig)

- OCR für gescannte Dokumente
- Bildanalyse für Foto-Belege
- Externe API für aktuelle Spesensätze
- Geocoding API für exakte Länderbestimmung
- Automatische Übersetzung bei fremdsprachigen Dokumenten
- Echtheitsprüfung mit ML-Modellen

