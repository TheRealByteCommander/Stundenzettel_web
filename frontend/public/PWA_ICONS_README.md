# PWA-Icons erstellen

Für die vollständige PWA-Funktionalität müssen die folgenden Icons erstellt werden:

## Benötigte Icons

1. **icon-192.png** (192x192px)
   - Für Android und Desktop
   - Format: PNG mit Transparenz
   - Verwendet in: manifest.json

2. **icon-512.png** (512x512px)
   - Für Android Splash Screen
   - Format: PNG mit Transparenz
   - Verwendet in: manifest.json

3. **apple-touch-icon.png** (180x180px)
   - Für iOS Home Screen
   - Format: PNG ohne Transparenz (iOS erwartet kein Alpha)
   - Verwendet in: index.html, manifest.json

## Design-Vorgaben

- **Hintergrundfarbe**: #e90118 (Brand-Primary)
- **Text/Logo**: Weiß oder kontrastreich
- **Stil**: Modern, minimalistisch, erkennbar auch bei kleinen Größen

## Tools zum Erstellen

- **Online**: https://realfavicongenerator.net/
- **Figma**: Design erstellen und exportieren
- **Photoshop/GIMP**: Manuell erstellen

## Platzierung

Alle Icons müssen im `frontend/public/` Verzeichnis platziert werden.

## Nach dem Erstellen

1. Icons in `frontend/public/` kopieren
2. Frontend neu bauen: `npm run build`
3. Auf iOS testen: "Zum Home-Bildschirm hinzufügen"
4. Auf Android testen: "Zur Startseite hinzufügen"

