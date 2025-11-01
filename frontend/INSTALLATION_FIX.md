# 🔧 Installation - Dependency-Konflikte beheben

## Problem

Beim `npm install` können Dependency-Konflikte auftreten:
- `react-day-picker@8.10.1` benötigt `date-fns@^2.28.0 || ^3.0.0`, aber es ist `date-fns@4.1.0` installiert
- ESLint-Versionen-Konflikte

## Lösung

Die `package.json` wurde bereits angepasst:
- `date-fns` wurde auf Version `^3.6.0` geändert (kompatibel mit `react-day-picker@8.10.1`)
- ESLint wurde auf Version `^8.57.0` geändert (kompatibel mit `react-scripts@5.0.1`)

## Installation

### Option 1: Mit `--legacy-peer-deps` (Empfohlen)

```bash
cd frontend
npm install --legacy-peer-deps
```

### Option 2: Mit Yarn (alternativ)

Da `package.json` bereits `packageManager: yarn` enthält:

```bash
cd frontend
yarn install
```

### Option 3: Clean Install

Falls Probleme bestehen:

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

## Verifizierung

Nach erfolgreicher Installation:

```bash
npm start
# Oder
yarn start
```

Die App sollte unter `http://localhost:3000` laufen.

## Troubleshooting

### Problem: "Cannot find module 'react-day-picker'"

Lösung: Prüfen Sie, ob `react-day-picker` in `node_modules` vorhanden ist:

```bash
cd frontend
ls node_modules | grep react-day-picker
```

Falls nicht vorhanden:
```bash
npm install react-day-picker@8.10.1 --legacy-peer-deps
```

### Problem: ESLint-Fehler beim Build

Die ESLint-Warnungen können ignoriert werden, da sie hauptsächlich Peer-Dependency-Warnungen sind. Der Build sollte trotzdem funktionieren.

### Problem: Date-Funktionen funktionieren nicht

Prüfen Sie die `date-fns` Version:

```bash
npm list date-fns
```

Sollte `date-fns@3.x.x` sein (nicht 4.x.x).

