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

### Iteration 3 – Timesheets ⏳ (laufend)
- [x] Liste & Detailansicht inkl. Statuswechsel (Send/Approve/Reject) und Mailversand.
- [x] Anlage neuer Stundenzettel mit grundlegender Formularlogik.
- [x] Upload unterschriebener PDFs inkl. Rückmeldung im Detail.
- [ ] Verifikationshinweise & Admin-spezifische Aktionen (z. B. QA-Notizen).
- [ ] Statistiken/Reporting (Monatsübersichten, Ranking).

## Arbeitspakete (Iteration 4 – Reisekosten**
1. **Reisekostenmodul**  
   - Genehmigte Stundenzettel importieren, Belege hochladen, Fremdwährungsnachweis.
   - Chat mit Agenten, Statuswechsel.

2. **Dokumenten-/Beleganalyse-UI**  
   - Darstellung extrahierter Daten, Validierungs-Hinweise.

## Arbeitspakete (Iteration 5 – Administration & Settings)
1. **Benutzerverwaltung**  
   - CRUD, Rollen, Wochenstunden.

2. **SMTP/Push/Einstellungen**  
   - Formulare & Validierung, Push-Registrierung.

3. **Sicherheit & Compliance**  
   - Rate-Limits, Audits, Datenschutz-Hinweise.

## Arbeitspakete (Iteration 6 – Abschluss)
1. **E2E-/Regressionstests**  
   - Realistische Szenarien automatisieren.
2. **Optimierungen/Refactoring**  
   - Performance, Bundle-Größe, Barrierefreiheit.
3. **Rollout-Plan**  
   - Deployment-Schritte, Migrationshinweise, Dokumentation.

## Nächste Schritte
1. Timesheet-Iteration abschließen: Upload unterschriebener PDFs, Admin-Notizen & Reporting integrieren.
2. Architekturplan um konkrete Modul-Routing-Aufteilung ergänzen (Timesheet-Unterseiten).
3. Vorbereitung Iteration 4 – Reisekosten (API-Clients ableiten, UI-Konzept entwerfen).

