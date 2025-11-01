# Sicherheitsmaßnahmen im Webinterface

## Implementierte Sicherheitsfeatures

### 1. XSS-Schutz (Cross-Site Scripting)
- ✅ **DOMPurify** für HTML-Sanitization
- ✅ Alle User-Inputs werden sanitized bevor sie gerendert werden
- ✅ `dangerouslySetInnerHTML` nur mit sanitized Content
- ✅ Eingeschränkte erlaubte HTML-Tags für Ankündigungen
- ✅ Event-Handler werden entfernt

**Erlaubte HTML-Tags für Ankündigungen:**
- Text-Formatierung: `p`, `br`, `strong`, `em`, `u`
- Überschriften: `h1` - `h6`
- Listen: `ul`, `ol`, `li`
- Links: `a` (nur mit `href`, `title`, `target`)

**Blockierte Elemente:**
- `<script>`, `<iframe>`, `<object>`, `<embed>`
- Event-Handler (`onclick`, `onerror`, etc.)
- `javascript:` Protocol
- Path Traversal

### 2. Input-Validierung und Sanitization
- ✅ E-Mail-Validierung mit Regex
- ✅ Passwort-Validierung (8-128 Zeichen)
- ✅ Längenlimits für alle Eingabefelder
- ✅ Dateinamen-Validierung (Path Traversal Prevention)
- ✅ HTML-Entität-Encoding

**Validierungsregeln:**
- E-Mail: Standard E-Mail-Format
- Passwort: 8-128 Zeichen
- Name: 2-100 Zeichen
- Titel: 3-200 Zeichen
- Nachrichten: Max 1000 Zeichen
- Dateinamen: Keine Path Traversal, keine Sonderzeichen

### 3. Token-Sicherheit
- ✅ Token mit Ablaufzeit (24 Stunden)
- ✅ Automatische Prüfung auf Ablauf
- ✅ Secure Storage-Funktionen
- ✅ Automatische Bereinigung bei Ablauf
- ✅ Axios Interceptor für automatische Token-Verwaltung

**Token-Handling:**
```javascript
// Token wird mit Expiration gespeichert
setSecureToken(token, 24); // 24 Stunden

// Token wird automatisch geprüft
const token = getSecureToken(); // null wenn abgelaufen

// Bei Logout werden alle Tokens gelöscht
clearSecureToken();
```

### 4. Rate Limiting (Client-Side)
- ✅ Login: Max 5 Versuche pro Minute
- ✅ Uploads: Max 10 pro Minute
- ✅ Chat-Nachrichten: Max 20 pro Minute
- ✅ Verhindert Brute-Force-Angriffe

### 5. File Upload Security
- ✅ Nur PDF-Dateien erlaubt
- ✅ Maximale Dateigröße: 10MB
- ✅ Dateinamen-Validierung (Path Traversal Prevention)
- ✅ Server-seitige Validierung (zusätzlich)

### 6. Axios Security Interceptors
- ✅ Automatisches Hinzufügen von Authorization-Header
- ✅ Automatische Token-Expiration-Behandlung
- ✅ Automatische Weiterleitung bei 401-Fehler

### 7. Content Security
- ✅ HTML-Content wird vor Rendering sanitized
- ✅ Base64-Bilder werden validiert
- ✅ Keine inline Scripts
- ✅ XSS-Protection Header

## Security Headers

Die folgenden Security Headers werden im HTML gesetzt:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

## Best Practices

### Für Entwickler

1. **Nie `dangerouslySetInnerHTML` ohne Sanitization verwenden**
   ```javascript
   // ❌ FALSCH
   <div dangerouslySetInnerHTML={{ __html: userInput }} />
   
   // ✅ RICHTIG
   <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(userInput) }} />
   ```

2. **Alle User-Inputs validieren und sanitizen**
   ```javascript
   const sanitized = sanitizeInput(userInput);
   if (!validateEmail(sanitized)) {
     // Error handling
   }
   ```

3. **Token immer mit Expiration speichern**
   ```javascript
   setSecureToken(token, 24); // Nicht localStorage.setItem direkt
   ```

4. **Rate Limiting bei sensiblen Operationen**
   ```javascript
   if (!checkRateLimit(5, 60000)) {
     // Block request
   }
   ```

## Bekannte Sicherheitsmerkmale

- ✅ Keine sensiblen Daten im Client-Code
- ✅ Keine Hardcoded-Credentials
- ✅ Backend-URL aus Umgebungsvariable
- ✅ Alle API-Calls über HTTPS (in Production)
- ✅ CSRF-Schutz im Backend (Token-basiert)

## Zusätzliche Empfehlungen

### Production Deployment:
1. **HTTPS erzwingen** (HTTP Strict Transport Security)
2. **Content Security Policy (CSP)** Header hinzufügen
3. **Subresource Integrity (SRI)** für externe Scripts
4. **Regelmäßige Security-Audits** durchführen

### Server-Konfiguration:
```nginx
# Nginx Beispiel
add_header X-Frame-Options "DENY";
add_header X-Content-Type-Options "nosniff";
add_header X-XSS-Protection "1; mode=block";
add_header Referrer-Policy "strict-origin-when-cross-origin";
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';";
```

## Reporting Security Issues

Bei gefundenen Sicherheitslücken bitte melden an:
- admin@schmitz-intralogistik.de
- Keine öffentliche Meldung ohne vorherige Absprache

