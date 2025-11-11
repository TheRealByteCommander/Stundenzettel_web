# Frontend-Neuaufbau – Zielarchitektur

_Iteration 1 – Architekturplanung (Stand: 2025-11-09)_

## 1. Technologiewahl

| Bereich | Entscheidung | Begründung |
|---------|--------------|-----------|
| Build-/Dev-Tool | **Vite + React 18 + TypeScript** | Schneller Dev-Server, lean Bundles, native ESM, integrierter TS-Support. |
| UI-Bibliothek | **Radix UI + TailwindCSS + shadcn/ui** | Kompatibel mit vorhandenem Look & Feel; Komponenten modular adaptierbar. |
| Formularhandling | **React Hook Form + Zod** | Typisierte Validierung, gute Performance, integrierbar mit bestehenden Inputs. |
| State Management | **React Query (Server State) + Zustand (UI/Session)** | Entkoppelt API-Daten (Queries/Mutations) von UI-Zustand; geringe Boilerplate. |
| Routing | **React Router v7** | Nested Routes, Data APIs; spaßorientiert für modulare Navigation. |
| HTTP | **Axios** (bereits etabliert); + zentrale API-Client-Schicht mit Interceptor. |
| Auth | **JWT + Refresh-Handling via React Query** | Bewahrt bestehende Backend-Struktur. |
| Testing | **Vitest + Testing Library** (Unit) / **Cypress** (E2E) | Moderne Toolchain, schnelle Feedback-Zyklen. |

## 2. Projektstruktur (Vorschlag)

```
frontend/
├─ src/
│  ├─ app/                # App-Shell, Routing, Layouts
│  │  ├─ App.tsx
│  │  ├─ routes.tsx
│  │  └─ providers.tsx    # QueryClientProvider, ThemeProvider, etc.
│  ├─ modules/
│  │  ├─ auth/
│  │  │  ├─ pages/        # Login, 2FA, PasswordChange
│  │  │  ├─ hooks/        # useLoginMutation, use2faSetup
│  │  │  └─ components/
│  │  ├─ dashboard/
│  │  ├─ timesheets/
│  │  ├─ expenses/
│  │  ├─ vacation/
│  │  ├─ admin/
│  │  └─ shared/          # domänenübergreifende Komponenten (Announcements, Chat)
│  ├─ services/
│  │  ├─ api/
│  │  │  ├─ client.ts     # axios instance + interceptors
│  │  │  ├─ endpoints.ts  # z.B. `getAnnouncements`
│  │  │  └─ types.ts      # DTOs (aus Backend-Modellen)
│  │  └─ adapters/        # helper (date, pdf download, notifications)
│  ├─ store/
│  │  ├─ auth-store.ts    # Zustand: token, user
│  │  ├─ ui-store.ts      # e.g. dialogs, theme
│  ├─ components/
│  │  ├─ ui/              # shadcn/ui re-exports
│  │  └─ layout/          # Header, Sidebar, MobileNav
│  ├─ lib/
│  │  ├─ utils.ts         # sanitize, format, etc.
│  │  └─ hooks/           # useDisclosure, useDebounce,...
│  ├─ assets/
│  ├─ styles/
│  ├─ test/
│  └─ main.tsx            # Einstieg
├─ public/
├─ vite.config.ts
├─ tsconfig.json
└─ package.json
```

## 3. Routing & Layout

### 3.1 Hauptlayouts
- **PublicLayout**: Login, 2FA-Setup, Passwortrücksetzung (später).
- **ProtectedLayout**: Authenticated Shell (Header, Sidebar, Mobile Drawer), prüft Rolle.
- **AdminLayout** (optional): Zusätzliche Navigationselemente für Admin-Routen.

### 3.2 Routenübersicht
| Route | Beschreibung | Zugriffsrolle |
|-------|--------------|---------------|
| `/login` | Auth-Einstieg, 2FA-Dialog | öffentlich |
| `/2fa/setup` | Pflichtsetup nach erstem Login | öffentlich (mit Temp-Token) |
| `/app` | Dashboard (Announcements, Statistiken) | user+ |
| `/app/timesheets` | Wochenübersicht, CRUD | user+ |
| `/app/expenses` | Reisekosten monatlich | user |
| `/app/vacation` | Urlaubsübersicht | user |
| `/app/accounting` | Accounting-Stats & Report-Download | accounting/admin |
| `/app/admin/users` | Benutzerverwaltung | admin |
| `/app/admin/announcements` | Ankündigungen verwalten | admin |
| `/app/admin/settings` | SMTP, Push | admin |

#### 3.2.1 Timesheet-Routing (Nested)
```
/app/timesheets
├─ (index)                 → `TimesheetListPage` (eigene Stundenzettel)
├─ /new                    → `TimesheetCreatePage`
├─ /:id                    → `TimesheetDetailPage`
└─ /admin/review           → `TimesheetAdminPage` (Buchhaltung/Admin)
```
- `TimesheetDetailPage` blendet Upload-Abschnitt für Mitarbeitende ein und zusätzlich Prüfbemerkungen für Rollen `admin`/`accounting`.
- Admin-Review erhält Query-Filter (`month`, später `userId`) und verlinkt in die Detailseite.
- Routing-Struktur dient als Referenz für spätere Unterrouten (z. B. `/admin/review/:id` falls Review-Workspace notwendig wird).

#### 3.2.2 Reisekosten-Routing (Ausblick)
```
/app/expenses
├─ (index)                 → Monatsübersicht & Report-Liste (React Query, Filter Select)
├─ /reports/:id            → Detailansicht mit Chat / Dokumentenprüfung
└─ /receipts/upload        → Dialog / Drawer für neuen Beleg (FormData Upload)
```
- Erstes Ziel Iteration 4: Index-Seite mit Liste genehmigter Stundenzettel + Upload-Schritt kombinieren.
- Detailroute kann später gestaffelt eingeführt werden; Placeholder-Komponenten werden im Modul angelegt.

> React Router bietet Loader/Action APIs; wir kombinieren es mit React Query (Queries/Mutations) für Datenfetching.

## 4. State-Management & Datenfluss

### 4.1 Authentifizierung
- **Zustand**: `auth-store` (Zustand) speichert `token`, `user`, `tempToken`, `otpRequired`.
- **Axios-Interceptor**: hängt JWT an, reagiert auf 401 → logout & Redirect.
- **Persistenz**: Token + Ablaufzeit in `localStorage` (verschlüsselt via vorhandenen Utilities oder WebCrypto).
- **React Query**: `useUserQuery()` (abhängig vom Token) aktualisiert globale Session.

### 4.2 Server State (React Query)
- Jede Modul-Funktionalität erhält eigene `queryKeys`:
  - `['announcements', { activeOnly }]`
  - `['timesheets', month]`, `['timesheet', id]`
  - `['expenseReports', month]`, `['expenseReport', id]`
  - `['vacation', 'requests']`, `['vacation', 'balance']`, …
- Mutationen invalidieren passende Queries.

### 4.3 Form-Zustand
- `react-hook-form` + `zod` Schema (z. B. LoginSchema, AnnouncementSchema).
- Bessere Typisierung & Fehlermeldungshandling; verringert manuelles `useState`.

### 4.4 UI-Zustand
- `Zustand`-Stores für modale Dialoge (z. B. 2FA-Dialog, PasswordDialog, AnnouncementDialog).
- Alternativ: `@radix-ui/react-dialog` Controlled Components mit dedizierten Hooks.

## 5. Services & Utilities

### 5.1 API-Client (Axios)
- `client.ts`: erstellt Instanz mit Basis-URL aus Env, Attach Token, Retry optional.
- `endpoints.ts`: typisierte Wrapper (z. B. `fetchAnnouncements(params)`, `updateAnnouncement(body)`).
- Consider `axios-middleware` für Error Handling (z. B. convert into `AppError`).

### 5.2 Sicherheits-Funktionen
- Reuse `sanitizeInput`, `checkRateLimit` (evtl. in `lib/security.ts`).
- DOMPurify nur an zentralen Stellen (z. B. `RichText`-Komponente).
- Input-Sanitizing & Zod `refine` für Passwörter, E-Mail etc.

### 5.3 Datei-Handling
- Utility `downloadBlob`, `openPdf`.
- Uploads über `FormData`-Mutationen, Retry mit Feedback.

### 5.4 Notifications
- Einheitliches Toast-System (`sonner` oder `@radix-ui/react-toast`).
- `useToast()` Hook in shared-Layer.

## 6. Styling & Design-System

- Tailwind Themes + CSS Variables (Primärfarbe #e90118 etc.).
- Komponentensammlung in `components/ui` (Buttons, Inputs, Cards, Tables) – generiert via shadcn, anschließend konsolidiert.
- Responsive Patterns: Layout mit CSS Grid/Flex, mobile Navigation via Drawer.
- Iconset: `lucide-react` (wie bisher).

## 7. Modul-Spezifische Hinweise

### 7.1 Auth
- Login-Seite mit `react-hook-form`.
- 2FA Setup/Verify als `Dialog` Komponente, gesteuert durch Mutationsergebnisse.
- Password Change → separater Page/Section (`/app/settings/security`?).

### 7.2 Timesheets
- Unterteilung: Liste (`TimesheetListPage`), Detail (`TimesheetDetailPage`), Editor (`TimesheetCreatePage`), Admin-Review (`TimesheetAdminPage`).
- Aktueller Stand: CRUD + Upload + Prüfbemerkungen vollständig; nächster Ausbauschritt Reporting/Exporte.
- Upload: eigener Abschnitt im Detail, Admin-Bereich ergänzt Verifikationsnotizen (persistiert via `PUT /timesheets/{id}`).
- Admin-Ansicht nutzt Query-Parameter (`month`, später `userId`) und Routelinks zu Details.

### 7.3 Expenses
- Monatliche Auswahl (Select) → Query.
- Beleg-Liste als Cards/Table; Chat-Sidebar.
- Zustand: dedizierter Query + Mutation Hooks (`useExpenseReports`, `useUploadReceipt`).

### 7.4 Vacation
- Tabs: Anträge, Guthaben, Anforderungen.
- Admin-Aktionen (Approve, Reject) mit Confirmation Dialogen.

### 7.5 Admin
- Angaben in Formularen mit `react-hook-form`.
- Diagramme/Statistiken optional (z. B. `@tanstack/react-charts` oder Recharts) – optionaler scope.

## 8. Internationalisierung & Lokalisierung
- Primäre Sprache Deutsch (wie bisher). Strings in separaten Konstanten („copy“ Datei) zur Wartbarkeit.
- Date/Number Format via `Intl` (z. B. `Intl.DateTimeFormat('de-DE')`).

## 9. Testing-Strategie
- **Unit**: Komponenten/Hooks (Vitest + RTL).
- **Integration**: Pages mit Mock-Service Worker (MSW).
- **E2E**: Critical Paths (Login + 2FA, Timesheet erstellen, Reisekosten hochladen, Admin-Announcement).
- **Smoke**: GitHub Actions Pipeline (optional).

## 10. Migration & Rollout (High-Level)
- Parallelbetrieb möglich: Backend APIs bleiben identisch → Feature-Flag für neues Frontend (z. B. `?new=`).
- Schrittweise Einführung: erst Auth + Dashboard, dann Timesheets etc.
- Datenkompatibilität prüfen (z. B. `announcement.image_url` — Backwards compatibility).

## 11. Offene Entscheidungen / ToDos
- Soll die App weiterhin als Single SPA laufen oder als Microfrontends modularisiert? (Empfehlung: SPA, modulare Struktur reicht.)
- Push-Integration: Prüfen, ob Workbox/Service Worker erneuert werden soll.
- PDF-Rendering & Download Handling (z. B. Browser-native vs. PDF.js?).
- Feature-Flag-Strategie definieren (z. B. LaunchDarkly / simple env-based).

---

**Nächste Aktion:** Umsetzung Iteration 1 abschließen, anschließend mit Modul _Auth & App Shell_ (Iteration 2) starten.

