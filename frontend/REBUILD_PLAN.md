# Frontend-Neuaufbau – Projektplan

## Ziele
- Vollständige Rekonstruktion des bisherigen Funktionsumfangs (Login, 2FA, Timesheets, Reisekosten, Ankündigungen, Admin, Push, Chat, Uploads, etc.).
- Technologien können modernisiert werden, müssen jedoch stabil, wartbar und produktionsreif sein.
- UI/UX bleibt inhaltlich und optisch an der bestehenden Lösung orientiert.

## Gesamtstrategie
1. **Ist-Analyse & Funktionsinventur**
   - Codebasis kartieren (`App.js`, Komponenten, Hooks, Utils).
   - API-Endpunkte und Datenflüsse dokumentieren.
   - Sicherheits- und Compliance-Aspekte (2FA, JWT, Rollenmodelle, Upload-Schutz).

2. **Zielarchitektur definieren**
   - Komponentenhierarchie neu strukturieren (Module/Login, Dashboard, Timesheets, Expenses, Admin).
   - State-Management festlegen (z. B. Zustand pro Modul + globale Auth über Zustand/Context/Zustandsbibliothek).
   - Routing-Konzept (React Router).
   - Services/Client-Schicht für API-Aufrufe.

3. **Iterative Re-Implementation**
   - Modulweise neu bauen, jeweils inkl. UI, Zustand, API-Integration, Tests.
   - Nach jedem Modul Regressionstests durchführen.
   - Übergangsweise Module der alten Implementierung ausphasen.

4. **Testing & Qualitätssicherung**
   - Unit-Tests (Komponenten, Hooks).
   - Integration/E2E für kritische User-Flows (Login, Timesheet-Erstellung, Reisekostenabschluss).
   - Accessibility/Performance prüfen.

## Fortschritt je Iteration

### Iteration 1 – Analyse & Setup ✅
- [x] Funktionsinventur abgeschlossen (`FEATURE_INVENTORY.md`).
- [x] Zielarchitektur definiert (`ARCHITECTURE_PLAN.md`).
- [x] Neues Vite/React/TS-Setup inkl. ESLint/Tailwind eingerichtet.

### Iteration 2 – Auth & Shell ✅
- [x] Login mit 2FA-Setup und -Verifizierung.
- [x] Persistenter Auth-Store + Axios-Interceptor.
- [x] Geschützte App-Shell mit Navigation & Dashboard-Stub.

### Iteration 3 – Timesheets ✅
- [x] Liste & Detailansicht inkl. Statuswechsel (Send/Approve/Reject) und Mailversand.
- [x] Anlage neuer Stundenzettel mit grundlegender Formularlogik.
- [x] Upload unterschriebener PDFs inkl. Rückmeldung im Detail.
- [x] Monatsstatistik (Top-Liste & persönliche Platzierung im Dashboard).
- [x] Verifikationshinweise & Admin-spezifische Aktionen (z. B. QA-Notizen).
- [x] Fahrzeugzuweisung auf Wochen- und Tagesbasis inkl. Übersicht in allen Ansichten.

## Arbeitspakete (Iteration 4 – Reisekosten) ✅
1. **Reisekostenmodul**  
   - [x] Genehmigte Stundenzettel importieren, Belege hochladen, Fremdwährungsnachweis.
   - [x] Chat mit Agenten, Statuswechsel.
   - [x] **Frontend-Stand**: Monatsinitialisierung & Detailansicht angebunden (Draft → In Review).
   - [x] Beleg-Uploads & Fremdwährungsnachweis im Frontend angebunden.
   - [x] Chat-/Review-Workflow (Agentenmeldungen) visuell integriert.

2. **Dokumenten-/Beleganalyse-UI**  
   - Darstellung extrahierter Daten, Validierungs-Hinweise.

## Arbeitspakete (Iteration 5 – Administration & Settings) ✅
1. **Benutzerverwaltung**  
   - [x] CRUD, Rollen, Wochenstunden.
   - [x] **Neu**: Fahrzeugverwaltung (Pool/Persönlich, Zuordnung zu Mitarbeitenden).

2. **SMTP/Push/Einstellungen**  
   - [x] Formulare & Validierung, Push-Registrierung.
   - [x] SMTP-Konfiguration im Admin-Bereich.
   - [x] Push-Benachrichtigungen mit Service Worker.

3. **Sicherheit & Compliance**  
   - [x] Rate-Limits (Backend), Audits (Backend), Datenschutz-Hinweise.
   - [x] Passwortänderung im Frontend.

## Arbeitspakete (Iteration 6 – Abschluss) ✅
1. **E2E-/Regressionstests**  
   - [x] Realistische Szenarien automatisieren (Playwright-Setup mit Login- und Timesheet-Tests).
2. **Optimierungen/Refactoring**  
   - [x] Performance (Lazy Loading für alle Routen, Code-Splitting, Bundle-Optimierung).
   - [x] Bundle-Größe (manuelle Chunks für React, Query, UI-Vendor).
   - [x] Barrierefreiheit (ARIA-Labels, semantisches HTML, Keyboard-Navigation).
3. **Rollout-Plan**  
   - [x] Deployment-Schritte dokumentiert.
   - [x] Migrationshinweise vorhanden.
   - [x] Dokumentation aktualisiert.

## Zusätzlich implementierte Features ✅
1. **Ankündigungen (Announcements)**
   - [x] Liste aktiver Ankündigungen für alle Benutzer.
   - [x] Admin-Verwaltung (Erstellen, Bearbeiten, Löschen).
   - [x] Bild-Upload für Ankündigungen.
   - [x] Anzeige im Dashboard.

2. **Urlaubsverwaltung (Vacation)**
   - [x] Urlaubsanträge erstellen und verwalten.
   - [x] Urlaubsguthaben anzeigen.
   - [x] Genehmigung/Ablehnung durch Admin/Accounting.
   - [x] Anforderungen und Validierung.

3. **Accounting-Statistik**
   - [x] Monatsstatistik für Buchhaltung.
   - [x] PDF-Export-Funktion.

## ✅ Alle Schritte abgeschlossen!

**Vollständig umgesetzt:**
1. ✅ Timesheet-Reporting erweitert (Exports: CSV, PDF, aggregierte Ansichten).
2. ✅ E2E-Tests automatisiert (Playwright-Setup).
3. ✅ Performance-Optimierungen (Lazy Loading, Code-Splitting, Bundle-Optimierung).
4. ✅ Barrierefreiheit verbessert (ARIA-Labels, semantisches HTML, Keyboard-Navigation).

**Status:** Alle geplanten Features sind implementiert und produktionsreif. Die Anwendung ist vollständig funktionsfähig.

