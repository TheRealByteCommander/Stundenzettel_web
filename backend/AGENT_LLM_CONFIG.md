# 🤖 LLM-Konfiguration für Agents

## Übersicht

Jeder Agent hat spezifische Aufgaben und Anforderungen. Daher sollten verschiedene LLMs für optimale Performance konfiguriert werden.

## Agent-spezifische LLM-Empfehlungen

### 1. ChatAgent 🗣️

**Aufgaben:**
- Dialoge mit Benutzern
- Rückfragen zu fehlenden Informationen
- Kommunikation auf Deutsch
- Kurze, präzise Antworten

**Anforderungen:**
- ✅ Schnelle Antwortzeiten (gute User Experience)
- ✅ Gute Deutschkenntnisse
- ✅ Verständliche, freundliche Kommunikation
- ✅ Kontextverständnis für Rückfragen

**Empfohlene LLMs (Priorität):**

1. **Qwen2.5:32B** ⭐⭐⭐⭐⭐ (Aktuell konfiguriert)
   - Größe: 32B Parameter
   - RAM: ~40GB
   - Geschwindigkeit: ⚡⚡ (schnell für 32B)
   - Qualität: ⭐⭐⭐⭐⭐ (exzellent)
   - **Warum:** Sehr starke Qualität für Dialoge, ausgezeichnete Deutschkenntnisse, hohe Kontextverarbeitung

**Konfiguration:**
```env
OLLAMA_MODEL_CHAT=Qwen2.5:32B
```

---

### 2. DocumentAgent 📄

**Aufgaben:**
- PDF-Analyse und Text-Extraktion
- Dokumenten-Kategorisierung (Hotel, Restaurant, Maut, etc.)
- Strukturierte Daten-Extraktion (Beträge, Daten, Steuernummern)
- Vollständigkeitsprüfung
- Validierung und Qualitätsprüfung
- JSON-Generierung
- **Optional:** Vision-Analyse für gescannte Dokumente/Foto-Belege (mit Vision-Modell)

**Anforderungen:**
- ✅ Hohe Präzision bei Datenextraktion
- ✅ Gute Strukturerkennung
- ✅ Zuverlässige JSON-Generierung
- ✅ Mehr Kontext für komplexe Dokumente
- ✅ Multilingual (internationale Belege)
- ✅ **Optional:** Bildverarbeitung für gescannte Dokumente/Fotos

**Empfohlene LLMs (Priorität):**

1. **Qwen2.5vl:7b** ⭐⭐⭐⭐⭐ (Aktuell konfiguriert)
   - Größe: 7B Parameter (mit Vision-Fähigkeiten)
   - RAM: ~10GB
   - Geschwindigkeit: ⚡⚡ (schnell)
   - Qualität: ⭐⭐⭐⭐⭐ (exzellent für Bilder und Dokumente)
   - **Warum:** **Vision-Modell für gescannte Dokumente und Foto-Belege** - kann Bilder direkt analysieren, sehr gute Datenextraktion aus Dokumenten
   - **Anwendung:** Ideal für PDFs, gescannte Dokumente und Foto-Belege

**Konfiguration:**
```env
OLLAMA_MODEL_DOCUMENT=Qwen2.5vl:7b
```

**Hinweis:** Qwen2.5vl ist ein Vision-Modell, das sowohl Text als auch Bilder verarbeiten kann. Es ist ideal für gescannte Dokumente, Foto-Belege und PDFs mit Bildern.

---

### 3. AccountingAgent 💰

**Aufgaben:**
- Dokument-Zuordnung zu Reiseeinträgen
- Kategorisierung (Hotel, Verpflegung, Transport, etc.)
- Verpflegungsmehraufwand-Berechnung
- Machbarkeitsprüfung (überlappende Hotels, Datum-Abgleich)
- Logik-Validierung
- Komplexe Entscheidungen
- Mathematische Berechnungen

**Anforderungen:**
- ✅ Sehr gute Logik-Fähigkeiten
- ✅ Mathematische Genauigkeit
- ✅ Komplexe Entscheidungsfindung
- ✅ Kontextverständnis für Zuordnungen
- ✅ Konsistenz-Prüfung

**Empfohlene LLMs (Priorität):**

1. **DeepSeek-R1:32B** ⭐⭐⭐⭐⭐ (Aktuell konfiguriert)
   - Größe: 32B Parameter (Reasoning-Modell)
   - RAM: ~40GB
   - Geschwindigkeit: ⚡⚡ (schnell für 32B)
   - Qualität: ⭐⭐⭐⭐⭐ (exzellent für Logik und Reasoning)
   - **Warum:** **Reasoning-Modell mit hervorragenden Logik-Fähigkeiten** - ideal für komplexe Entscheidungen, mathematische Berechnungen, Zuordnungen und Machbarkeitsprüfungen
   - **Anwendung:** Perfekt für buchhaltungsrelevante Aufgaben mit hohen Anforderungen an Logik und Genauigkeit

**Konfiguration:**
```env
OLLAMA_MODEL_ACCOUNTING=DeepSeek-R1:32B
```

**Hinweis:** DeepSeek-R1 ist speziell für Reasoning-Aufgaben optimiert und bietet ausgezeichnete Logik-Fähigkeiten für komplexe Buchhaltungsaufgaben.

---

## Konfiguration

### 1. Environment-Variablen (.env Datei)

Erstellen Sie eine `.env` Datei im `backend/` Verzeichnis:

```env
# Ollama Server (GMKTec evo x2)
OLLAMA_BASE_URL=http://192.168.178.155:11434

# Standard-Modell (Fallback)
OLLAMA_MODEL=Qwen2.5:32B

# Agent-spezifische Modelle
OLLAMA_MODEL_CHAT=Qwen2.5:32B
OLLAMA_MODEL_DOCUMENT=Qwen2.5vl:7b
OLLAMA_MODEL_ACCOUNTING=DeepSeek-R1:32B

# Timeout-Konfiguration (länger für große Modelle)
OLLAMA_TIMEOUT=600
OLLAMA_MAX_RETRIES=3
OLLAMA_RETRY_DELAY=2.0
```

### 2. Docker Compose (docker-compose.agents.yml)

```yaml
environment:
  # Ollama Server
  - OLLAMA_BASE_URL=${OLLAMA_BASE_URL:-http://192.168.178.155:11434}
  
  # Agent-spezifische Modelle
  - OLLAMA_MODEL=${OLLAMA_MODEL:-Qwen2.5:32B}
  - OLLAMA_MODEL_CHAT=${OLLAMA_MODEL_CHAT:-Qwen2.5:32B}
  - OLLAMA_MODEL_DOCUMENT=${OLLAMA_MODEL_DOCUMENT:-Qwen2.5vl:7b}
  - OLLAMA_MODEL_ACCOUNTING=${OLLAMA_MODEL_ACCOUNTING:-DeepSeek-R1:32B}
  
  # Timeout-Konfiguration (länger für große Modelle)
  - OLLAMA_TIMEOUT=${OLLAMA_TIMEOUT:-600}
  - OLLAMA_MAX_RETRIES=${OLLAMA_MAX_RETRIES:-3}
  - OLLAMA_RETRY_DELAY=${OLLAMA_RETRY_DELAY:-2.0}
```

### 3. Direkt in agents.py

Die Konfiguration erfolgt über Environment-Variablen (Zeilen 42-46):

```python
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'Qwen2.5:32B')
OLLAMA_MODEL_CHAT = os.getenv('OLLAMA_MODEL_CHAT', OLLAMA_MODEL)
OLLAMA_MODEL_DOCUMENT = os.getenv('OLLAMA_MODEL_DOCUMENT', OLLAMA_MODEL)
OLLAMA_MODEL_ACCOUNTING = os.getenv('OLLAMA_MODEL_ACCOUNTING', OLLAMA_MODEL)
```

**Hinweis:** Ändern Sie nicht direkt `agents.py`, sondern verwenden Sie Environment-Variablen!

---

## Modell-Download auf GMKTec evo x2

Laden Sie die empfohlenen Modelle auf Ihrem GMKTec-Server herunter:

```bash
# Auf GMKTec evo x2 Rechner

# ChatAgent (32B Modell - hohe Qualität)
ollama pull Qwen2.5:32B

# DocumentAgent (Vision-Modell - für Dokumente und Bilder)
ollama pull Qwen2.5vl:7b

# AccountingAgent (Reasoning-Modell - stark bei Logik)
ollama pull DeepSeek-R1:32B
```

**Wichtig:** Diese Modelle benötigen ausreichend RAM:
- Qwen2.5:32B: ~40GB RAM
- Qwen2.5vl:7b: ~10GB RAM
- DeepSeek-R1:32B: ~40GB RAM

**Gesamt:** Empfohlen mindestens 64GB+ RAM für gleichzeitige Nutzung

**Prüfen Sie verfügbare Modelle:**
```bash
ollama list
```

---

## Empfohlene Konfigurationen

### Aktuelle Konfiguration (64GB+ RAM empfohlen) ⭐ **AKTUELL VERWENDET**

```env
OLLAMA_MODEL_CHAT=Qwen2.5:32B           # ~40GB RAM
OLLAMA_MODEL_DOCUMENT=Qwen2.5vl:7b      # ~10GB RAM
OLLAMA_MODEL_ACCOUNTING=DeepSeek-R1:32B # ~40GB RAM
```
**Gesamt:** ~50GB RAM (wenn Modelle nicht gleichzeitig geladen sind), bis zu ~90GB bei gleichzeitiger Nutzung

**Vorteile:**
- Sehr hohe Qualität für alle Agenten
- Vision-Unterstützung für Dokumente und Bilder
- Exzellente Reasoning-Fähigkeiten für Buchhaltung
- Beste Ergebnisse bei komplexen Fällen

**Nachteile:**
- Hohe Ressourcen-Anforderungen (mindestens 64GB RAM empfohlen)
- Langsamere Antwortzeiten als kleinere Modelle
- Benötigt leistungsstarke Hardware

**Hinweis:** Die aktuellen Modelle sind für maximale Qualität optimiert. Für ressourcen-effizientere Alternativen siehe Abschnitt "Empfohlene LLMs" bei jedem Agent.

---

## Performance-Optimierung

### Timeout-Konfiguration

Größere Modelle (32B Parameter) benötigen deutlich mehr Zeit:

```env
# Für große Modelle (32B Parameter - Standard für aktuelle Konfiguration)
OLLAMA_TIMEOUT=600

# Für sehr große Modelle oder komplexe Anfragen
OLLAMA_TIMEOUT=900

# Für kleinere Modelle (falls gewechselt wird)
# OLLAMA_TIMEOUT=300
```

### Retry-Konfiguration

Für stabileres Netzwerk:

```env
OLLAMA_MAX_RETRIES=5
OLLAMA_RETRY_DELAY=3.0
```

---

## Testen der Konfiguration

### 1. Health Check

```bash
# Von Proxmox-Server
curl http://192.168.178.155:11434/api/tags
```

### 2. Test einzelner Agents

```python
from agents import OllamaLLM

# ChatAgent
chat_llm = OllamaLLM(base_url="http://192.168.178.155:11434", model="Qwen2.5:32B")
response = await chat_llm.chat([{"role": "user", "content": "Hallo!"}])
print(f"ChatAgent: {response[:100]}")

# DocumentAgent
doc_llm = OllamaLLM(base_url="http://192.168.178.155:11434", model="Qwen2.5vl:7b")
response = await doc_llm.chat([{"role": "user", "content": "Analysiere Dokument..."}])
print(f"DocumentAgent: {response[:100]}")

# AccountingAgent
acc_llm = OllamaLLM(base_url="http://192.168.178.155:11434", model="DeepSeek-R1:32B")
response = await acc_llm.chat([{"role": "user", "content": "Ordne Dokument zu..."}])
print(f"AccountingAgent: {response[:100]}")
```

### 3. Logs überprüfen

```bash
# Im Agent-Container
docker logs stundenzettel-agents | grep "Ollama LLM erreichbar"
```

Sie sollten sehen:
```
✅ Ollama LLM erreichbar für ChatAgent: http://192.168.178.155:11434 (Modell: Qwen2.5:32B)
✅ Ollama LLM erreichbar für DocumentAgent: http://192.168.178.155:11434 (Modell: Qwen2.5vl:7b)
✅ Ollama LLM erreichbar für AccountingAgent: http://192.168.178.155:11434 (Modell: DeepSeek-R1:32B)
```

---

## Zusammenfassung

| Agent | Aktuelles Modell | RAM | Priorität |
|-------|-------------------|-----|-----------|
| **ChatAgent** | Qwen2.5:32B | ~40GB | Hohe Qualität für Dialoge |
| **DocumentAgent** | Qwen2.5vl:7b | ~10GB | **Vision-Modell für Dokumente und Bilder** |
| **AccountingAgent** | DeepSeek-R1:32B | ~40GB | **Reasoning-Modell für komplexe Logik** |

**Aktuelle Konfiguration:**
```env
OLLAMA_MODEL_CHAT=Qwen2.5:32B
OLLAMA_MODEL_DOCUMENT=Qwen2.5vl:7b
OLLAMA_MODEL_ACCOUNTING=DeepSeek-R1:32B
```

**Hinweis:** Diese Konfiguration ist für maximale Qualität optimiert und benötigt mindestens 64GB+ RAM.

**Speicherort:**
- `.env` Datei im `backend/` Verzeichnis
- Oder Environment-Variablen in `docker-compose.agents.yml`

---

**Hinweis:** Starten Sie den Agent-Container nach Änderungen neu:
```bash
docker compose -f docker-compose.agents.yml restart
```
