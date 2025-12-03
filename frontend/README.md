# Tick Guard Frontend (Rebuild)

Neuer React/Vite/TypeScript-Client für Tick Guard. Die bisherigen shadcn/CRA-Bestände sind unter `frontend_legacy/` archiviert und dienen nur noch als Referenz während der Migration.

## Technologie-Stack

- [Vite](https://vitejs.dev/) + React 19 + TypeScript
- TailwindCSS 3 & eigene UI-Komponenten (Button, Card, etc.)
- Zustand (Session-State) & TanStack Query (Server-State)
- React Router v7
- Axios-basierter API-Client mit JWT/2FA-Unterstützung

Architektur- und Migrationsdetails: siehe  
- `ARCHITECTURE_PLAN.md`  
- `REBUILD_PLAN.md`  
- `FEATURE_INVENTORY.md`

## Setup

```bash
# Install dependencies
npm install

# Lokaler Dev-Server
npm run dev

# Typprüfung + Build
npm run build

# Linting
npm run lint
```

Vite benötigt Node ≥ 20.19 oder ≥ 22.12 (Hinweis wird aktuell auf Node 20.15 noch angezeigt).

## Konfiguration

Die folgenden Variablen werden per `.env` (nicht versioniert) erwartet:

```
VITE_API_BASE_URL=http://192.168.178.157:8000/api
VITE_DEFAULT_ADMIN_EMAIL=admin@schmitz-intralogistik.de
VITE_DEFAULT_ADMIN_PASSWORD=admin123
```

Für lokale Tests kann eine Kopie von `.env.example` angelegt werden.

## Implementierungsstand

✅ **Vollständig implementiert** - Alle Features aus dem Rebuild-Plan sind umgesetzt:

### ✅ Iteration 1-3 – Basis & Timesheets:
- Login mit E-Mail/Passwort + Validierung  
- 2FA-Flow (Verify & Initial Setup inkl. QR)  
- Session-Persistenz via Zustand  
- Geschütztes Layout inkl. Logout  
- React Query / Axios Client + Interceptoren  
- Liste, Detailansicht & Erstellung von Wochen-Stundenzetteln  
- Statuswechsel (Entwurf → gesendet → genehmigt), Mailversand  
- Upload unterschriebener PDF-Stundenzettel mit Feedback  
- Monatsstatistik inkl. persönlicher Platzierung auf dem Dashboard  
- Admin-/Buchhaltungsansicht zur manuellen Prüfung und Genehmigung
- Fahrzeugzuordnung pro Woche und optional pro Tag (inkl. Anzeige in allen Ansichten)
- **Timesheet-Reporting**: Export-Funktionen (CSV, PDF), aggregierte Ansichten

### ✅ Iteration 4 – Reisekosten:
- Monatsübersicht (`/app/expenses`) mit Stundenzettel-Kopplung  
- Initialisierung monatlicher Reisekostenberichte (Auto-Befüllung aus genehmigten Wochen)  
- Detailansicht inkl. Statuswechsel Draft → In Review
- Beleg-Uploads & Fremdwährungsnachweis
- Chat-/Review-Workflow (Agentenmeldungen) visuell integriert
- API-Clients/Hooks für Reports, Belege & Chat vollständig implementiert

### ✅ Iteration 5 – Administration & Settings:
- **Benutzerverwaltung**: CRUD, Rollen, Wochenstunden
- **Fahrzeugverwaltung**: Pool-/Mitarbeiterfahrzeuge, Kennzeichenpflege, Zuordnung
- **SMTP-Konfiguration**: Admin-Interface für E-Mail-Einstellungen
- **Push-Benachrichtigungen**: Service Worker und Registrierung
- **Passwortänderung**: Dialog-Komponente
- **Accounting-Statistik**: Monatsstatistik und PDF-Export

### ✅ Zusätzliche Features:
- **Ankündigungen (Announcements)**: CRUD, Bild-Upload, Dashboard-Integration
- **Urlaubsverwaltung (Vacation)**: Anträge, Guthaben, Genehmigung, Anforderungen

### ✅ Qualitätssicherung:
- **E2E-Tests**: Playwright-Setup mit Login- und Timesheet-Tests
- **Performance-Optimierungen**: Lazy Loading, Code-Splitting, Bundle-Optimierung
- **Barrierefreiheit**: ARIA-Labels, semantisches HTML, Keyboard-Navigation

Alle Module sind vollständig implementiert und produktionsreif.
