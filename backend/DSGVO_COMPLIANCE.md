# DSGVO und EU-AI-Act Compliance

## Übersicht

Dieses System ist konform mit:
- **DSGVO** (Datenschutz-Grundverordnung)
- **EU-AI-Act** (Verordnung über Künstliche Intelligenz)

## DSGVO-Compliance Maßnahmen

### 1. Lokale Speicherung (Art. 5 Abs. 1 f)
- ✅ **Dokumente werden NUR auf lokalem Office-Rechner gespeichert**
- ✅ Keine Speicherung auf Webserver
- ✅ Validierung verhindert Webserver-Speicherung
- ✅ Konfiguration via `LOCAL_RECEIPTS_PATH` in `.env`

### 2. Verschlüsselung (Art. 32)
- ✅ **Automatische Verschlüsselung** aller hochgeladenen Dokumente
- ✅ Verschlüsselungsschlüssel aus Umgebungsvariable `ENCRYPTION_KEY`
- ✅ Fernet-Symmetric-Encryption (AES-128)
- ✅ Dateien werden beim Upload automatisch verschlüsselt

**Konfiguration:**
```env
ENCRYPTION_KEY=your-44-character-base64-encoded-key-here
```

**WICHTIG:** Schlüssel muss sicher gespeichert werden und darf NICHT ins Repository!

### 3. Audit-Logging (Art. 5 Abs. 2)
- ✅ **Vollständiges Audit-Log** aller Datenzugriffe
- ✅ Protokollierung: Upload, Download, Löschung, Änderung
- ✅ Speicherung in `backend/logs/audit.log`
- ✅ Enthält: Timestamp, User-ID, Aktion, Ressource

### 4. Aufbewahrungsfristen (Art. 5 Abs. 1 e)
- ✅ **Automatische Löschung** nach Aufbewahrungsfrist
- ✅ Genehmigte Abrechnungen: 10 Jahre (GoBD)
- ✅ Entwürfe/Abgelehnte: 1 Jahr
- ✅ Automatische Bereinigung via `RetentionManager`

**Aufbewahrungsfristen:**
```python
RETENTION_PERIOD_RECEIPTS_DAYS = 10 * 365  # 10 Jahre (GoBD)
RETENTION_PERIOD_DRAFT_DAYS = 365          # 1 Jahr
RETENTION_PERIOD_APPROVED_DAYS = 10 * 365  # 10 Jahre
```

### 5. Datenminimierung (Art. 5 Abs. 1 c)
- ✅ Nur notwendige Daten werden gespeichert
- ✅ PDF-Belege: Nur Original-Dateien, keine Duplikate
- ✅ Metadaten: Minimale Erfassung (ID, Dateiname, Größe, Datum)

### 6. Zweckbindung (Art. 5 Abs. 1 b)
- ✅ Daten werden nur für Reisekostenabrechnung verwendet
- ✅ Keine Weitergabe an Dritte
- ✅ Klar definierter Verwendungszweck

### 7. Zugriffskontrolle (Art. 32)
- ✅ Rollenbasierte Zugriffskontrolle
- ✅ Nur autorisierte Benutzer können Dokumente hochladen/sehen
- ✅ Audit-Log protokolliert alle Zugriffe

## EU-AI-Act Compliance

### 1. Transparenz (Art. 13)
- ✅ **AI-Entscheidungen werden vollständig dokumentiert**
- ✅ Logging aller AI-Entscheidungen mit:
  - Agent-Name
  - AI-Modell
  - Eingabedaten (Hash für Datenschutz)
  - Entscheidungsergebnis
  - Konfidenz-Wert
  - Menschliche Überprüfung (Ja/Nein)

### 2. Recht auf Auskunft (Art. 13)
- ✅ Benutzer können Einblick in AI-Entscheidungen erhalten
- ✅ AI-Decision-Logs werden mit Reports gespeichert
- ✅ API-Endpoint für Auskunft über AI-Entscheidungen

### 3. Menschliche Aufsicht (Art. 14)
- ✅ Alle AI-Entscheidungen können von Buchhaltung überprüft werden
- ✅ Status "In Prüfung" ermöglicht menschliche Kontrolle
- ✅ Chat-Interface für Rückfragen

### 4. Dokumentation (Art. 11)
- ✅ Alle AI-Entscheidungen werden dokumentiert
- ✅ Entscheidungsgrundlagen werden gespeichert
- ✅ Nachvollziehbarkeit gewährleistet

## Konfiguration

### Erforderliche Umgebungsvariablen

```env
# Lokaler Speicherpfad (MUSS auf Office-Rechner zeigen, NICHT Webserver!)
LOCAL_RECEIPTS_PATH=C:/Reisekosten_Belege

# Verschlüsselungsschlüssel (WICHTIG: Sicher speichern!)
ENCRYPTION_KEY=generate-with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Ollama LLM (für AI-Agenten)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### Verschlüsselungsschlüssel generieren

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**WICHTIG:** 
- Schlüssel sicher speichern (z.B. in verschlüsseltem Password-Manager)
- Bei Verlust können verschlüsselte Dateien NICHT wiederhergestellt werden!
- NICHT ins Git-Repository committen!

## Audit-Log Analyse

Audit-Logs befinden sich in: `backend/logs/audit.log`

Format (JSON):
```json
{
  "timestamp": "2024-01-01T12:00:00",
  "action": "upload",
  "user_id": "user-123",
  "resource_type": "receipt",
  "resource_id": "receipt-456",
  "details": {"filename": "hotel.pdf", "encrypted": true}
}
```

## Retention Management

Automatische Löschung abgelaufener Dateien:
- Wird beim Server-Start initialisiert
- Sollte regelmäßig ausgeführt werden (z.B. täglich via Cronjob)

```python
from compliance import RetentionManager
deleted_count = await retention_manager.delete_expired_files()
```

## Datenschutzerklärung für Benutzer

### Welche Daten werden gespeichert?
- Hochgeladene PDF-Belege (verschlüsselt, nur lokal)
- Metadaten (Dateiname, Größe, Upload-Datum)
- AI-Entscheidungen (für Transparenz)

### Wo werden Daten gespeichert?
- **NUR auf lokalem Office-Rechner** (nicht auf Webserver)
- Verschlüsselt gespeichert
- Keine Cloud-Speicherung

### Wer hat Zugriff?
- Nur autorisierte Benutzer (Rollen: User, Admin, Buchhaltung)
- Alle Zugriffe werden protokolliert

### Wie lange werden Daten gespeichert?
- Genehmigte Abrechnungen: 10 Jahre (gesetzliche Aufbewahrungspflicht)
- Entwürfe: 1 Jahr
- Automatische Löschung nach Frist

### Ihre Rechte (DSGVO Art. 15-22):
- ✅ Auskunft über gespeicherte Daten
- ✅ Berichtigung falscher Daten
- ✅ Löschung (nach Ablauf Aufbewahrungsfrist)
- ✅ Datenübertragbarkeit
- ✅ Widerspruch gegen Verarbeitung

### AI-Verarbeitung (EU-AI-Act):
- ✅ Transparenz: Sie werden über AI-Entscheidungen informiert
- ✅ Auskunft: Sie können Entscheidungsgrundlagen erfragen
- ✅ Widerspruch: Sie können AI-Entscheidungen widersprechen
- ✅ Menschliche Prüfung: Alle Entscheidungen werden geprüft

## Kontakt

Bei Fragen zum Datenschutz oder AI-Verarbeitung:
- Administrator: admin@schmitz-intralogistik.de
- Datenschutzbeauftragter: [Kontakt einfügen]

