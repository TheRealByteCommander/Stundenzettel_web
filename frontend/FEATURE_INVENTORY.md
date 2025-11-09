# Frontend Funktionsinventur (Stand: Neuaufbauplanung)

> **Rebuild-Status (Nov 2025)**  
> - Auth & App-Shell: ✓ vollständig umgesetzt  
> - Timesheets: Liste, Detail, Erstellung & Monatsstatistik ✓ – Admin-Notizen & erweiterte Reports folgen  
> - Übrige Module (Reisekosten, Urlaub, Admin, Push) folgen in kommenden Iterationen

Dieses Dokument katalogisiert den aktuellen Funktionsumfang der bestehenden React-Anwendung sowie die angebundenen API-Endpunkte und Kern-Datenmodelle. Grundlage sind `frontend/src/App.js` und die FastAPI-Definitionen in `backend/server.py`. Diese Inventur dient als Referenz für den schrittweisen Neuaufbau.

---

## 1. Funktionsmodule & Features

### 1.1 Auth & Sicherheit
- Login mit E-Mail/Passwort (`/auth/login`), clientseitige Validierung & Rate-Limit.
- Obligatorisches 2FA:
  - Setup-Flow mit QR-Code (`/auth/2fa/setup-qr`, `/auth/2fa/initial-setup`).
  - Regelmäßige Verifizierung (`/auth/2fa/verify`).
- Passwortänderung über Dialog (`/auth/change-password`).
- Token-Verwaltung (lokaler Secure Storage, Auto-Attach in Axios-Interceptor).
- Push-Benachrichtigungen:
  - Öffentlichen Schlüssel laden (`/push/public-key`).
  - Subscription registrieren (`/push/subscribe`).
- Logout mit vollständiger Token-Säuberung.

### 1.2 Dashboard & Ankündigungen
- Anzeige aktiver Ankündigungen beim Login (`/announcements?active_only=true`).
- Admin-Dialog zum Verwalten:
  - Auflisten, Erstellen, Bearbeiten, Löschen (`/announcements`, `/announcements/{id}`).
  - Bild-Upload (`/announcements/upload-image`).
  - Sanitizing & HTML-Vorschau.
- Schnellzugriff auf Benutzeranleitung (GitHub-Link).

### 1.3 Stundenzettel (Timesheets)
- Wochenübersicht mit automatischer Wochendatums-Berechnung.
- CRUD für Wochen-Stundenzettel (`/timesheets`, `/timesheets/{id}`).
- E-Mail-Versand an Vorgesetzte (`/timesheets/{id}/send-email`).
- Download/Versand von unterschriebenen PDF-Dateien (`/timesheets/{id}/download-and-email`).
- Upload unterschriebener Stundenzettel (`/timesheets/{id}/upload-signed`).
- Admin-Workflows:
  - Genehmigen/Ablehnen (`/timesheets/{id}/approve`, `/timesheets/{id}/reject`).
  - Übersicht für Buchhaltung (`/accounting/timesheets-list`) inkl. manueller Prüfung.
  - Löschen (Admin) (`/timesheets/{id}` DELETE).
- Statistiken & Ranglisten:
  - Monatsstunden je Nutzer (`/stats/monthly`).
  - Rangposition (`/stats/monthly/rank`).

### 1.4 Reisekosten (Expenses)
- Monatsauswahl mit Verfügbarkeit (`/travel-expense-reports/available-months`).
- Reisekostenbericht initialisieren, laden, aktualisieren (`/travel-expense-reports`, `/travel-expense-reports/{id}`).
- Beleg-Uploads (PDF), automatische Analyse, Fremdwährungsnachweis:
  - Upload (`/travel-expense-reports/{id}/receipts`).
  - Fremdwährungsnachweis hochladen (`/travel-expense-reports/{id}/receipts/{receiptId}/exchange-proof`).
  - Beleg löschen (`/travel-expense-reports/{id}/receipts/{receiptId}`).
- Chat mit Agent*innen (`/travel-expense-reports/{id}/chat` senden & abrufen).
- Abrechnung abschließen (`/travel-expense-reports/{id}/submit`).

### 1.5 Urlaubsverwaltung
- Anzeige offener Urlaubsanträge (`/vacation/requests`).
- Urlaubsguthaben je Jahr (`/vacation/balance`).
- Anforderungen/Kriterien pro Jahr (`/vacation/requirements/{year}`).
- Antrag anlegen/löschen (`/vacation/requests` POST / DELETE).
- Genehmigen/Ablehnen (`/vacation/requests/{id}/approve`, `/.../reject`).
- Admin-Löschung (`/vacation/requests/{id}/admin-delete`).
- Anpassung Urlaubstage (`/vacation/balance/{user}/{year}`).

### 1.6 Benutzer- & Systemeinstellungen (Admin)
- Nutzerverwaltung:
  - Liste, Erstellung, Bearbeitung, Löschung (`/users`, `/auth/register`, `/users/{id}`).
  - Rollen (user/admin/accounting), Wochenstunden.
- SMTP-Konfiguration für E-Mails (`/admin/smtp-config` GET/POST).
- Accounting-Statistik:
  - Monatsdaten für Buchhaltung (`/accounting/monthly-stats`).
  - PDF-Export (`/accounting/monthly-report-pdf`).

### 1.7 Push & Service Worker
- Prüft Unterstützungsstatus, holt VAPID-Key, registriert Browser-Push, speichert Subscriptions.

### 1.8 UI & Interaktion
- Verwendung von shadcn/ui Komponenten (Tabs, Cards, Dialoge, Select, Table etc.).
- Mobile Navigation (Hamburger-Menü) & App-Wechsel (Timesheets ↔ Expenses).
- Toast/Alert Meldungen für Erfolg/Fehler (eigener Hook plus UI).

---

## 2. API-Endpunkte (aus Frontend-Sicht)

| Methode | Pfad | Zweck | Request-Payload | Relevante Response-Felder |
|---------|------|-------|-----------------|---------------------------|
| GET | `/auth/me` | Session validieren / Userdaten | Token im Header | `id`, `email`, `name`, `role`, `is_admin` |
| POST | `/auth/login` | Login & 2FA-Trigger | `{ email, password }` | `access_token` ODER `requires_2fa`, `temp_token`, `requires_2fa_setup` |
| POST | `/auth/2fa/setup-qr` | QR-Code URL für 2FA | `setup_token` (query) | `otpauth_uri` |
| POST | `/auth/2fa/initial-setup` | Abschluss 2FA-Setup | `{ otp, temp_token }` | `access_token`, `user` |
| POST | `/auth/2fa/verify` | 2FA-Login-Schritt | `{ otp, temp_token }` | `access_token`, `user` |
| POST | `/auth/change-password` | Passwort ändern | `{ current_password, new_password }` | `message` |
| POST | `/auth/register` | Benutzer anlegen (Admin) | `{ email, name, password, role, weekly_hours }` | `user_id` |
| GET | `/users` | Benutzerliste | – | Array `[{ id, email, name, role, is_admin }]` |
| PUT | `/users/{id}` | Benutzer aktualisieren | Felder aus `UserUpdate` | `message` |
| DELETE | `/users/{id}` | Benutzer löschen | – | `message` |
| GET | `/timesheets` | Stundenzettelübersicht | Query optional? (aktueller Nutzer) | Liste `WeeklyTimesheet` |
| POST | `/timesheets` | Stundenzettel speichern | `WeeklyTimesheetCreate` | `message` / aktualisierte Daten |
| POST | `/timesheets/{id}/send-email` | PDF-Mail versenden | `{ recipients }` optional | `message` |
| POST | `/timesheets/{id}/download-and-email` | Download & Mail | – | `file` / `message` |
| POST | `/timesheets/{id}/upload-signed` | Unterschriebenen Zettel hochladen | `multipart/form-data` | `message`, `accounting_users_notified` |
| POST | `/timesheets/{id}/approve` | Stundenzettel genehmigen | – | `message` |
| POST | `/timesheets/{id}/reject` | Stundenzettel ablehnen | `{ reason? }` optional | `message` |
| DELETE | `/timesheets/{id}` | Stundenzettel löschen | – | `message` |
| GET | `/stats/monthly` | Monatsstatistik | `?month=YYYY-MM` | `stats` (Stunden pro Nutzer) |
| GET | `/stats/monthly/rank` | Ranginformation | `?month=YYYY-MM` | `rank`, `total_users` |
| GET | `/accounting/monthly-stats` | Buchhaltungs-Übersicht | `?month=YYYY-MM` | Aggregierte Reisekosten/Zeiten |
| GET | `/accounting/monthly-report-pdf` | PDF-Report | `?month=YYYY-MM` | PDF-Stream |
| GET | `/announcements` | Ankündigungen | `?active_only=true` | Liste `Announcement` |
| POST | `/announcements` | Ankündigung erstellen | `AnnouncementCreate` | `Announcement` |
| PUT | `/announcements/{id}` | Ankündigung aktualisieren | `AnnouncementUpdate` | `Announcement` |
| DELETE | `/announcements/{id}` | Ankündigung löschen | – | `message` |
| POST | `/announcements/upload-image` | Bild hochladen | `multipart/form-data` | `image_url`, `image_filename` |
| GET | `/push/public-key` | VAPID-Key | – | `publicKey` |
| POST | `/push/subscribe` | Push-Subscription speichern | `{ endpoint, keys }` | `status` |
| POST | `/push/unsubscribe` | Subscription löschen | `{ endpoint }` | `status` |
| GET | `/vacation/requests` | Urlaubsanträge | – | Liste `VacationRequest` |
| POST | `/vacation/requests` | Antrag anlegen | `VacationRequestCreate` | `message` |
| DELETE | `/vacation/requests/{id}` | Antrag löschen (self) | – | `message` |
| POST | `/vacation/requests/{id}/approve` | Antrag genehmigen | – | `message` |
| POST | `/vacation/requests/{id}/reject` | Antrag ablehnen | – | `message` |
| DELETE | `/vacation/requests/{id}/admin-delete` | Admin-Löschung | – | `message` |
| GET | `/vacation/balance` | Urlaubskonto | `?year=YYYY` optional | Liste `VacationBalance` |
| PUT | `/vacation/balance/{userId}/{year}` | Urlaubsguthaben anpassen | `{ total_days }` | `message` |
| GET | `/vacation/requirements/{year}` | Anforderungen (Minima, Deadlines) | – | `requirements` |
| GET | `/travel-expense-reports/available-months` | Monate mit Reports | – | `[{ value, label }]` |
| GET | `/travel-expense-reports` | Reports für Nutzer | `?month=` | Liste `TravelExpenseReport` |
| POST | `/travel-expense-reports` | Report initialisieren | `{ month }` | `report` |
| GET | `/travel-expense-reports/{id}` | Report-Detail | – | `TravelExpenseReport` |
| PUT | `/travel-expense-reports/{id}` | Report aktualisieren | `TravelExpenseReportUpdate` | `report` |
| POST | `/travel-expense-reports/{id}/submit` | Abrechnung abschließen | – | `message` |
| POST | `/travel-expense-reports/{id}/receipts` | Beleg hochladen | `multipart/form-data` | `receipt`, `has_issues` |
| DELETE | `/travel-expense-reports/{id}/receipts/{receiptId}` | Beleg löschen | – | `message` |
| POST | `/travel-expense-reports/{id}/receipts/{receiptId}/exchange-proof` | Fremdwährungsnachweis | `multipart/form-data` | `message` |
| GET | `/travel-expense-reports/{id}/chat` | Chatverlauf | – | Nachrichtenliste |
| POST | `/travel-expense-reports/{id}/chat` | Nachricht senden | `{ message }` | `chat_message` |
| GET | `/admin/smtp-config` | SMTP-Daten abrufen | – | `smtp_server`, `smtp_port`, … |
| POST | `/admin/smtp-config` | SMTP speichern | `SMTPConfigCreate` | `message` |

> Hinweis: Die Tabelle konzentriert sich auf Endpunkte, die das aktuelle Frontend konsumiert. Die Backend-API bietet darüber hinaus Funktionen (Web Push an Rollen, Agents, etc.), die im Frontend (noch) nicht direkt aufgerufen werden.

---

## 3. Relevante Datenmodelle (Auszug aus `backend/server.py`)

- **User**
  - Felder: `id`, `email`, `name`, `role` (`user|admin|accounting`), `hashed_password`, `two_fa_secret`, `two_fa_enabled`, `weekly_hours`, `is_admin` (legacy).

- **WeeklyTimesheet / TimeEntry**
  - Timesheet: `id`, `user_id`, `user_name`, `week_start`, `week_end`, `entries`, `status`, `signed_pdf_path`, `signed_pdf_verified`, `signed_pdf_verification_notes`.
  - Entry: `date`, `start_time`, `end_time`, `break_minutes`, `tasks`, `customer_project`, `location`, `absence_type`, `travel_time_minutes`, `include_travel_time`.

- **TravelExpenseReport / TravelExpenseReportEntry / TravelExpenseReceipt**
  - Report: `id`, `user_id`, `user_name`, `month`, `entries`, `receipts`, `status`, `review_notes`, `accounting_data`, `document_analyses`.
  - Entry: `date`, `location`, `customer_project`, `travel_time_minutes`, `days_count`, `working_hours`.
  - Receipt: `id`, `filename`, `local_path`, `uploaded_at`, `file_size`, `exchange_proof_path`, `exchange_proof_filename`.

- **TravelExpense**
  - Einzelner Reisekosten-Eintrag (separat zum Report, z.B. in API).

- **VacationRequest / VacationBalance / VacationRequirements**
  - Request: `id`, `user_id`, `user_name`, `start_date`, `end_date`, `working_days`, `year`, `status`, `notes`.
  - Balance: `id`, `user_id`, `user_name`, `year`, `total_days`, `used_days`.
  - Requirements: `min_total_days`, `min_consecutive_days`, `deadline`, `meets_min_total`, `needs_reminder`, etc.

- **Announcement**
  - Felder: `id`, `title`, `content`, `image_url`, `image_filename`, `active`, `created_at`, `updated_at`, `created_by`.

- **SMTPConfig**
  - Felder: `smtp_server`, `smtp_port`, `smtp_username`, `smtp_password`, `admin_email`.

- **AccountingMonthlyStat**
  - Felder: `user_id`, `user_name`, `month`, `total_hours`, `hours_on_timesheets`, `travel_hours`, `travel_hours_on_timesheets`, `travel_kilometers`, `travel_expenses`, `timesheets_count`.

- **PushSubscription**
  - Felder: `endpoint`, `keys`, `user_id`, `role`.

---

## 4. Offene Fragen / ToDos für den Neuaufbau (Iteration 1)
- Genauere UI-Flows dokumentieren (Screenshots/Mockups) – optional.
- Klären, ob weitere, ungenutzte APIs berücksichtigt werden müssen (z. B. Agents, PDF-Generator).
- Festlegen des neuen Framework-Stacks (React + Vite? Next.js?).
- Entscheidung über State-Management (Zustand/Zustandsmaschinen).
- Migrationsstrategie für Bestandsdaten (z. B. Ankündigungsbilder, Beleg-Dateien).

Diese Inventur bildet die Grundlage für die Architekturplanung des Neuaufbaus.

