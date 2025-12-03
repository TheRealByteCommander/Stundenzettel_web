#!/usr/bin/env node

/**
 * Skript zum Generieren von PWA-Icons aus SVG
 * 
 * Benötigt: sharp (npm install sharp --save-dev)
 * 
 * Verwendung: node scripts/generate-icons.js
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Prüfe ob sharp installiert ist
let sharp;
try {
  const sharpModule = await import('sharp');
  sharp = sharpModule.default || sharpModule;
} catch (e) {
  console.error('❌ Fehler: sharp ist nicht installiert.');
  console.error('📦 Installiere es mit: npm install sharp --save-dev');
  console.error('   Oder verwende ein Online-Tool wie https://realfavicongenerator.net/');
  console.error('   Fehlerdetails:', e.message);
  process.exit(1);
}

const publicDir = path.join(__dirname, '..', 'public');
const svgPath = path.join(publicDir, 'icon.svg');

// Prüfe ob SVG existiert
if (!fs.existsSync(svgPath)) {
  console.error(`❌ SVG-Datei nicht gefunden: ${svgPath}`);
  process.exit(1);
}

const sizes = [
  { name: 'icon-192.png', size: 192 },
  { name: 'icon-512.png', size: 512 },
  { name: 'apple-touch-icon.png', size: 180 },
];

async function generateIcons() {
  console.log('🎨 Generiere PWA-Icons...\n');

  try {
    const svgBuffer = fs.readFileSync(svgPath);

    for (const { name, size } of sizes) {
      const outputPath = path.join(publicDir, name);
      
      await sharp(svgBuffer)
        .resize(size, size, {
          fit: 'contain',
          background: { r: 233, g: 1, b: 24, alpha: 1 } // #e90118
        })
        .png()
        .toFile(outputPath);

      console.log(`✅ ${name} (${size}x${size}) erstellt`);
    }

    console.log('\n✨ Alle Icons erfolgreich generiert!');
    console.log('📱 Die Icons sind jetzt in frontend/public/ verfügbar.');
  } catch (error) {
    console.error('❌ Fehler beim Generieren der Icons:', error.message);
    process.exit(1);
  }
}

generateIcons();

