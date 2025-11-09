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
VITE_API_BASE_URL=http://192.168.178.151:8000/api
VITE_DEFAULT_ADMIN_EMAIL=admin@schmitz-intralogistik.de
VITE_DEFAULT_ADMIN_PASSWORD=admin123
```

Für lokale Tests kann eine Kopie von `.env.example` angelegt werden.

## Implementierungsstand

✅ Iteration 2 – Auth & App-Shell:

- Login mit E-Mail/Passwort + Validierung  
- 2FA-Flow (Verify & Initial Setup inkl. QR)  
- Session-Persistenz via Zustand  
- Geschütztes Layout inkl. Logout  
- React Query / Axios Client + Interceptoren  

✅ Iteration 3 (Teilumfang) – Timesheets:

- Liste, Detailansicht & Erstellung von Wochen-Stundenzetteln  
- Statuswechsel (Entwurf → gesendet → genehmigt), Mailversand  
- Upload unterschriebener PDF-Stundenzettel mit Feedback

Weitere Module (Timesheet-Reporting, Reisekosten, Admin, …) werden gemäß Roadmap sukzessive migriert.
