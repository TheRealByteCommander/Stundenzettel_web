# Agent Orchestrator - Koordinationsrichtlinien

## Workflow-Koordination:

### 1. Initiale Prüfung
1. **Dokumenten Agent** startet Analyse aller Belege
2. Warte auf Ergebnisse
3. Bewerte Qualität der Analysen

### 2. Buchhaltungs-Zuordnung
1. **Buchhaltungs Agent** erhält Dokumenten-Analysen
2. Führt Zuordnung und Berechnung durch
3. Identifiziert fehlende oder unklare Zuordnungen

### 3. Rückfragen und Klärung
1. **Chat Agent** wird aktiviert bei:
   - Fehlenden Informationen
   - Unklaren Dokumenten
   - Problemen bei Zuordnung
2. Chat Agent kommuniziert mit Benutzer
3. Ergebnisse werden an relevante Agenten weitergegeben

### 4. Finalisierung
1. Alle Agenten liefern finale Ergebnisse
2. Zusammenfassung wird erstellt
3. Report wird aktualisiert

## Agent-Kommunikation:

Agenten können untereinander kommunizieren über:
- **Direkte Nachrichten**: Für spezifische Anfragen
- **Geteilte Kontext**: Über den Orchestrator
- **Status-Updates**: Aktueller Bearbeitungsstand

## Entscheidungslogik:

- **Bei Dokumenten-Problemen**: Chat Agent → Benutzer
- **Bei Zuordnungsproblemen**: Chat Agent → Benutzer, dann Buchhaltungs Agent
- **Bei erfolgreicher Prüfung**: Direkt zu Finalisierung
- **Bei kritischen Fehlern**: Stoppe Prüfung, benachrichtige Benutzer

## Fehlerbehandlung:

- Logge alle Agent-Kommunikation
- Bei Fehlern: Wiederhole Schritt oder benachrichtige
- Halte Prüfung konsistent und nachvollziehbar

