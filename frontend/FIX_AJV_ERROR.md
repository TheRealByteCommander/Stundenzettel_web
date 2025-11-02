# 🔧 Fix: "Cannot find module 'ajv/dist/compile/codegen'"

## Problem

Der Fehler tritt auf, wenn `ajv-keywords` eine neuere Version von `ajv` erwartet, aber eine inkompatible Version installiert ist.

## Lösung

### Option 1: Schnelle Lösung (Empfohlen)

```powershell
cd frontend

# ajv explizit installieren
npm install ajv@^8.12.0 --save-dev --legacy-peer-deps

# Dependencies neu installieren
npm install --legacy-peer-deps

# Cache löschen
Remove-Item -Recurse -Force node_modules\.cache -ErrorAction SilentlyContinue

# Server starten
npm start
```

### Option 2: Clean Install (falls Option 1 nicht funktioniert)

```powershell
cd frontend

# Alles löschen
Remove-Item -Recurse -Force node_modules, package-lock.json, node_modules\.cache -ErrorAction SilentlyContinue

# Neu installieren
npm install --legacy-peer-deps

# Server starten
npm start
```

### Option 3: Yarn verwenden (Alternative)

```powershell
cd frontend

# Yarn installieren (falls nicht vorhanden)
npm install -g yarn

# Mit Yarn installieren
yarn install

# Server starten
yarn start
```

## Was wurde geändert?

Die `package.json` wurde aktualisiert:
- `ajv@^8.12.0` wurde zu `devDependencies` hinzugefügt
- `resolutions` Feld hinzugefügt, um die ajv-Version zu erzwingen

## Verifizierung

Nach der Installation sollte der Server starten:

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

1. **Node.js-Version prüfen:**
   ```powershell
   node --version
   ```
   Sollte v18.x.x oder höher sein (v20.x.x ist auch OK)

2. **npm Cache leeren:**
   ```powershell
   npm cache clean --force
   ```

3. **Vollständiger Clean Install:**
   ```powershell
   cd frontend
   Remove-Item -Recurse -Force node_modules, package-lock.json -ErrorAction SilentlyContinue
   npm cache clean --force
   npm install --legacy-peer-deps
   npm start
   ```

## Ursache

Dieser Fehler tritt auf, weil:
- `react-scripts@5.0.1` verwendet `ajv-keywords`, das eine neuere Version von `ajv` benötigt
- Durch Dependency-Resolution kann eine inkompatible Version installiert werden
- `ajv@8.x` hat eine andere Modulstruktur als `ajv@6.x`

Die Lösung ist, `ajv@^8.12.0` explizit zu installieren.

