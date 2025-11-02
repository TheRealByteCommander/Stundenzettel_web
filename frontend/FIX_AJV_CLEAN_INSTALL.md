# 🔧 AJV-Fehler beheben - Clean Install Anleitung

## Problem

Der Fehler `Cannot find module 'ajv/dist/compile/codegen'` tritt auf, weil es einen Konflikt zwischen `ajv@6.x` und `ajv@8.x` gibt.

## Lösung: Clean Install

**WICHTIG:** Führen Sie diese Schritte in der angegebenen Reihenfolge aus!

### Schritt 1: Alle Dependencies löschen

```powershell
cd "C:\Users\mschm\OneDrive\Familienbereich\Dokumente\Stundenzettel_web-main\frontend"

# Alle node_modules und Locks löschen
Remove-Item -Recurse -Force node_modules, package-lock.json, yarn.lock -ErrorAction SilentlyContinue

# Cache löschen
Remove-Item -Recurse -Force node_modules\.cache -ErrorAction SilentlyContinue
npm cache clean --force
```

### Schritt 2: package.json prüfen

Stellen Sie sicher, dass `package.json` `ajv@^8.12.0` in `devDependencies` enthält:

```json
{
  "devDependencies": {
    "ajv": "^8.12.0",
    ...
  }
}
```

### Schritt 3: Neu installieren

```powershell
# Mit npm installieren (verwendet --legacy-peer-deps)
npm install --legacy-peer-deps
```

### Schritt 4: Server starten

```powershell
npm start
```

## Alternative: Mit Yarn (wenn npm nicht funktioniert)

Yarn hat bessere Dependency-Resolution:

```powershell
# Yarn installieren (falls nicht vorhanden)
npm install -g yarn

# Mit Yarn installieren
yarn install

# Server starten
yarn start
```

## Wenn es immer noch nicht funktioniert

### Option 1: Overrides in package.json

Fügen Sie `overrides` Feld hinzu (npm 8.3+):

```json
{
  "overrides": {
    "ajv": "^8.12.0"
  }
}
```

### Option 2: .npmrc Datei erstellen

Erstellen Sie `.npmrc` im `frontend/` Verzeichnis:

```
legacy-peer-deps=true
```

Dann:
```powershell
npm install
npm start
```

### Option 3: ajv-keywords aktualisieren

Manchmal hilft es, `ajv-keywords` auf eine neuere Version zu aktualisieren:

```powershell
npm install ajv-keywords@latest --legacy-peer-deps
```

## Verifikation

Nach erfolgreicher Installation sollte `npm start` folgendes zeigen:

```
Compiled successfully!

You can now view frontend in the browser.

  Local:            http://localhost:3000
```

## Was wurde geändert?

1. ✅ `ajv@^8.12.0` zu `devDependencies` hinzugefügt
2. ✅ `resolutions` Feld hinzugefügt (für Yarn)
3. ✅ Clean Install durchgeführt

## Ursache

- `react-scripts@5.0.1` verwendet `schema-utils@4.3.0`, das `ajv-keywords@5.1.0` benötigt
- `ajv-keywords@5.1.0` benötigt `ajv@^8.8.2`
- Aber viele andere Pakete verwenden noch `ajv@6.x`
- npm versucht beide Versionen zu installieren, was zu Konflikten führt

Die Lösung ist, `ajv@8.x` explizit zu installieren und einen Clean Install durchzuführen.

