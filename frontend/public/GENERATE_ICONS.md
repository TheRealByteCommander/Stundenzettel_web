# PWA-Icons generieren

## Option 1: Automatisch mit Node.js (Empfohlen)

### Voraussetzungen
```bash
cd frontend
npm install sharp --save-dev
```

### Icons generieren
```bash
npm run generate-icons
```

Das Skript generiert automatisch:
- `icon-192.png` (192x192px)
- `icon-512.png` (512x512px)
- `apple-touch-icon.png` (180x180px)

## Option 2: Online-Tool verwenden

1. Gehe zu https://realfavicongenerator.net/
2. Lade `icon.svg` hoch
3. Generiere die Icons
4. Lade die generierten Icons herunter
5. Platziere sie in `frontend/public/`:
   - `icon-192.png`
   - `icon-512.png`
   - `apple-touch-icon.png`

## Option 3: Manuell mit ImageMagick

```bash
# ImageMagick installieren (falls nicht vorhanden)
# Windows: choco install imagemagick
# macOS: brew install imagemagick
# Linux: sudo apt-get install imagemagick

cd frontend/public

# Generiere Icons
magick icon.svg -resize 192x192 icon-192.png
magick icon.svg -resize 512x512 icon-512.png
magick icon.svg -resize 180x180 apple-touch-icon.png
```

## Option 4: Mit Inkscape (Linux/macOS)

```bash
cd frontend/public

inkscape icon.svg --export-width=192 --export-filename=icon-192.png
inkscape icon.svg --export-width=512 --export-filename=icon-512.png
inkscape icon.svg --export-width=180 --export-filename=apple-touch-icon.png
```

## SVG-Dateien

- `icon.svg` - Haupt-Icon (komplexer)
- `icon-simple.svg` - Einfacheres Icon (Alternative)

Du kannst beide SVG-Dateien bearbeiten, um das Design anzupassen.

## Design-Anpassung

Die SVG-Dateien können mit jedem Vektor-Editor bearbeitet werden:
- **Online**: https://boxy-svg.com/ oder https://vectr.com/
- **Desktop**: Inkscape (kostenlos), Adobe Illustrator, Figma

### Farben ändern
- Hintergrund: `fill="#e90118"` (Brand-Primary)
- Icon: `stroke="white"` (Weiß)

### Größe anpassen
- ViewBox: `viewBox="0 0 512 512"`
- Transform: `transform="translate(256, 256)"` (Zentrierung)

