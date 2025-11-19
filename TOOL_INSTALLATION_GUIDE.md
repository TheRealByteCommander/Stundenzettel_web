# Tool-Installations-Guide

## Übersicht

Dieses Dokument beschreibt, wie alle optionalen Agent-Tools installiert werden können.

## Installations-Optionen

### 1. Vollständige Installation aller Tools

```bash
INSTALL_PRIO1_TOOLS=true \
INSTALL_PRIO2_TOOLS=true \
INSTALL_PRIO3_TOOLS=true \
INSTALL_EXA_TOOL=true \
INSTALL_PADDLEOCR=true \
INSTALL_LANGCHAIN=true \
EXA_API_KEY=your_key \
./scripts/install_backend_ct.sh
```

### 2. Schrittweise Installation nach Priorität

#### Priorität 1 Tools (empfohlen)
```bash
INSTALL_PRIO1_TOOLS=true ./scripts/install_backend_ct.sh
```

**Installiert:**
- `imagehash` - Für DuplicateDetectionTool (Perceptual Hash)
- `opencv-python` - Für ImageQualityTool
- `pytz` - Für TimeZoneTool
- `timezonefinder` - Für TimeZoneTool (erweiterte Zeitzonen-Erkennung)
- `dnspython` - Für EmailValidatorTool (DNS MX-Record-Prüfung)

#### Priorität 2 Tools
```bash
INSTALL_PRIO2_TOOLS=true ./scripts/install_backend_ct.sh
```

**Installiert:**
- `imapclient` - Für EmailParserTool (E-Mail-Parsing)
- `openpyxl` - Für ExcelImportExportTool (Excel-Dateien)
- `phonenumbers` - Für PhoneNumberValidatorTool (Telefonnummer-Validierung)
- `holidays` - Bereits in requirements.txt enthalten

#### Priorität 3 Tools
```bash
INSTALL_PRIO3_TOOLS=true ./scripts/install_backend_ct.sh
```

**Installiert:**
- `libzbar0` und `zbar-tools` (System-Paket) - Für pyzbar
- `pyzbar` - Für QRCodeReaderTool und BarcodeReaderTool
- `pillow` - Für QR-Code/Barcode-Erkennung (Bildverarbeitung)
- `opencv-python` - Sollte bereits für Priorität 1 Tools installiert sein

### 3. Einzelne Tools installieren

#### Exa/XNG Search Tool
```bash
INSTALL_EXA_TOOL=true EXA_API_KEY=your_key ./scripts/install_backend_ct.sh
```

#### PaddleOCR (OCR-Fallback)
```bash
INSTALL_PADDLEOCR=true ./scripts/install_backend_ct.sh
```

#### LangChain (erweiterte Workflows)
```bash
INSTALL_LANGCHAIN=true ./scripts/install_backend_ct.sh
```

## System-Abhängigkeiten

### Für Priorität 3 Tools (QR/Barcode-Erkennung)
- `libzbar0` - ZBar-Bibliothek (wird automatisch installiert)
- `zbar-tools` - ZBar-Tools (wird automatisch installiert)

## Tool-Status nach Installation

### Priorität 1 Tools (5 Tools)
- ✅ **DuplicateDetectionTool** - Erfordert: `imagehash`
- ✅ **IBANValidatorTool** - Keine zusätzlichen Abhängigkeiten
- ✅ **ImageQualityTool** - Erfordert: `opencv-python`, `numpy` (bereits vorhanden)
- ✅ **TimeZoneTool** - Erfordert: `pytz`, `timezonefinder`
- ✅ **EmailValidatorTool** - Erfordert: `dnspython`

### Priorität 2 Tools (9 Tools)
- ✅ **EmailParserTool** - Erfordert: `imapclient`
- ✅ **SignatureDetectionTool** - Erfordert: `PyPDF2` (bereits vorhanden)
- ✅ **ExcelImportExportTool** - Erfordert: `openpyxl`
- ✅ **PostalCodeValidatorTool** - Keine zusätzlichen Abhängigkeiten
- ✅ **PhoneNumberValidatorTool** - Erfordert: `phonenumbers`
- ✅ **HolidayAPITool** - Erfordert: `holidays` (bereits in requirements.txt)
- ✅ **WeatherAPITool** - Erfordert: `aiohttp` (bereits vorhanden)
- ✅ **TravelTimeCalculatorTool** - Erfordert: `aiohttp` (bereits vorhanden)
- ✅ **PDFTimestampTool** - Erfordert: `PyPDF2`/`pdfplumber` (bereits vorhanden)

### Priorität 3 Tools (9 Tools)
- ✅ **QRCodeReaderTool** - Erfordert: `pyzbar`, `pillow`, `opencv-python`
- ✅ **BarcodeReaderTool** - Erfordert: `pyzbar`, `opencv-python`
- ✅ **InvoiceNumberValidatorTool** - Keine zusätzlichen Abhängigkeiten
- ✅ **VATCalculatorTool** - Keine zusätzlichen Abhängigkeiten
- ✅ **ExpenseCategoryClassifierTool** - Keine zusätzlichen Abhängigkeiten
- ✅ **ReceiptStandardValidatorTool** - Keine zusätzlichen Abhängigkeiten
- ✅ **BankStatementParserTool** - Erfordert: `pdfplumber` (bereits vorhanden)
- ✅ **DistanceMatrixTool** - Nutzt TravelTimeCalculatorTool
- ✅ **CompanyDatabaseTool** - Erfordert: `aiohttp` (bereits vorhanden)

## API-Keys und Konfiguration

Nach der Installation müssen folgende API-Keys in der `.env`-Datei gesetzt werden (optional):

```bash
# Exa/XNG Search
EXA_API_KEY=your_exa_api_key_here

# Marker (erweiterte Dokumentenanalyse)
MARKER_API_KEY=your_marker_api_key_here
MARKER_BASE_URL=https://api.marker.io/v1

# DeepL (Übersetzungen)
DEEPL_API_KEY=your_deepl_api_key_here

# Wetter-API
WEATHER_API_KEY=your_weather_api_key_here
WEATHER_API_PROVIDER=openweathermap  # oder weatherapi

# Google Maps (optional)
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# OpenRouteService (kostenlos, empfohlen)
OPENROUTESERVICE_API_KEY=your_ors_api_key_here

# Web Access (Sicherheit)
WEB_ACCESS_ALLOWED_DOMAINS=example.com,api.example.com
WEB_ACCESS_BLOCKED_DOMAINS=localhost,127.0.0.1,0.0.0.0
```

## Verifikation

Nach der Installation können Sie prüfen, ob alle Tools verfügbar sind:

```bash
# Im Backend-Verzeichnis
cd /opt/tick-guard/Stundenzettel_web/backend
source venv/bin/activate

# Prüfe einzelne Pakete
python3 -c "import imagehash; print('imagehash OK')"
python3 -c "import cv2; print('opencv-python OK')"
python3 -c "import pytz; print('pytz OK')"
python3 -c "import timezonefinder; print('timezonefinder OK')"
python3 -c "import dns.resolver; print('dnspython OK')"
python3 -c "import imapclient; print('imapclient OK')"
python3 -c "import openpyxl; print('openpyxl OK')"
python3 -c "import phonenumbers; print('phonenumbers OK')"
python3 -c "from pyzbar import decode; print('pyzbar OK')"
python3 -c "from PIL import Image; print('pillow OK')"
```

## Fehlerbehebung

### pyzbar Installation schlägt fehl
- Stellen Sie sicher, dass `libzbar0` und `zbar-tools` installiert sind
- `apt-get install -y libzbar0 zbar-tools`

### opencv-python Installation schlägt fehl
- Stellen Sie sicher, dass alle Build-Abhängigkeiten installiert sind
- `apt-get install -y python3-dev build-essential`

### PaddleOCR Installation schlägt fehl
- PaddleOCR benötigt viele Abhängigkeiten
- Installation kann mehrere Minuten dauern
- Bei Problemen: PaddleOCR ist optional (Fallback-Tool)

## Zusammenfassung

**Gesamt: 23 neue Tools implementiert**
- Priorität 1: 5 Tools
- Priorität 2: 9 Tools
- Priorität 3: 9 Tools

Alle Tools sind optional und können schrittweise installiert werden. Die Basis-Funktionalität funktioniert auch ohne die optionalen Tools.

