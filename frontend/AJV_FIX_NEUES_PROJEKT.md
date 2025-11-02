# 🔧 AJV-Fehler beheben - Für neues Projekt-Verzeichnis

## Problem

Der Fehler `Cannot find module 'ajv/dist/compile/codegen'` tritt auf, weil `ajv-keywords` eine neuere Version von `ajv` erwartet, aber eine inkompatible Version installiert ist.

## Lösung

**Führen Sie diese Befehle in PowerShell im Frontend-Verzeichnis aus:**

```powershell
cd "C:\Users\mschm\OneDrive\Familienbereich\Dokumente\Stundenzettel_web-2025\Stundenzettel_web-main\frontend"

# 1. ajv explizit installieren
npm install ajv@^8.12.0 --save-dev --legacy-peer-deps

# 2. Cache löschen
Remove-Item -Recurse -Force node_modules\.cache -ErrorAction SilentlyContinue

# 3. Dependencies neu installieren
npm install --legacy-peer-deps

# 4. Server starten
npm start
```

## Alternative: Clean Install (falls oben nicht funktioniert)

```powershell
cd "C:\Users\mschm\OneDrive\Familienbereich\Dokumente\Stundenzettel_web-2025\Stundenzettel_web-main\frontend"

# Alles löschen
Remove-Item -Recurse -Force node_modules, package-lock.json -ErrorAction SilentlyContinue

# Cache löschen
npm cache clean --force

# Neu installieren
npm install --legacy-peer-deps

# Server starten
npm start
```

## Prüfen ob package.json korrekt ist

Die `package.json` sollte `ajv@^8.12.0` in `devDependencies` enthalten:

```json
{
  "devDependencies": {
    "ajv": "^8.12.0",
    ...
  }
}
```

Falls nicht vorhanden, fügen Sie es manuell hinzu oder verwenden Sie den ersten Befehl oben.

## Verifizierung

Nach erfolgreicher Installation sollte `npm start` ohne Fehler laufen:

```powershell
npm start
```

Erwartete Ausgabe:
```
Compiled successfully!

You can now view frontend in the browser.
  Local:            http://localhost:3000
```

## Wenn es weiterhin nicht funktioniert

### Option 1: .npmrc Datei erstellen

Erstellen Sie eine `.npmrc` Datei im `frontend/` Verzeichnis:

```
legacy-peer-deps=true
```

Dann:
```powershell
npm install
npm start
```

### Option 2: Yarn verwenden

```powershell
# Yarn installieren (falls nicht vorhanden)
npm install -g yarn

# Mit Yarn installieren (hat bessere Dependency-Resolution)
yarn install

# Server starten
yarn start
```

## Ursache

- `react-scripts@5.0.1` verwendet `schema-utils@4.3.0`, das `ajv-keywords@5.1.0` benötigt
- `ajv-keywords@5.1.0` benötigt `ajv@^8.8.2`
- Aber viele andere Pakete verwenden noch `ajv@6.x`
- npm versucht beide Versionen zu installieren, was zu Konflikten führt

Die Lösung ist, `ajv@8.x` explizit zu installieren und `--legacy-peer-deps` zu verwenden.

