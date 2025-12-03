# Frontend neu starten / aktualisieren

## Auf dem Server (Production)

### Option 1: Update-Script verwenden (Empfohlen)
```bash
# SSH zum Frontend-CT (192.168.178.156)
ssh root@192.168.178.156

# Update-Script ausführen
cd /opt/tick-guard/Stundenzettel_web
bash scripts/update_frontend.sh
```

Das Script:
- Führt `git pull` aus
- Installiert neue Abhängigkeiten (falls `package.json` geändert wurde)
- Baut das Frontend (`npm run build`)
- Deployt den Build nach `/var/www/tick-guard`
- Lädt Nginx neu (`systemctl reload nginx`)

### Option 2: Manuell neu bauen und deployen
```bash
# SSH zum Frontend-CT
ssh root@192.168.178.156

# Ins Frontend-Verzeichnis wechseln
cd /opt/tick-guard/Stundenzettel_web/frontend

# Git Pull (falls Änderungen vorhanden)
git pull origin main

# Abhängigkeiten installieren (falls nötig)
npm install --legacy-peer-deps

# Frontend bauen
npm run build

# Build deployen
rsync -a --delete build/ /var/www/tick-guard/
chown -R www-data:www-data /var/www/tick-guard

# Nginx neu laden
systemctl reload nginx
```

### Option 3: Nur Nginx neu laden (bei statischen Änderungen)
```bash
# SSH zum Frontend-CT
ssh root@192.168.178.156

# Nginx-Konfiguration testen
nginx -t

# Nginx neu laden (ohne Downtime)
systemctl reload nginx

# Oder Nginx komplett neu starten
systemctl restart nginx
```

## Lokal (Development)

### Development-Server starten
```bash
cd frontend
npm run dev
```

Der Dev-Server läuft auf `http://localhost:5173` (oder ähnlich) und lädt automatisch neu bei Änderungen.

### Development-Server stoppen
- `Ctrl+C` im Terminal

### Production-Build lokal testen
```bash
cd frontend

# Build erstellen
npm run build

# Preview-Server starten
npm run preview
```

## Troubleshooting

### Frontend lädt nicht / zeigt alte Version
```bash
# Browser-Cache leeren
# Oder Hard Refresh: Ctrl+Shift+R (Windows/Linux) oder Cmd+Shift+R (Mac)

# Auf dem Server: Nginx-Cache prüfen
systemctl status nginx
tail -f /var/log/nginx/error.log
```

### Build schlägt fehl
```bash
cd frontend

# Node-Module neu installieren
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps

# Build erneut versuchen
npm run build
```

### Nginx-Fehler
```bash
# Nginx-Konfiguration testen
nginx -t

# Nginx-Logs prüfen
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log

# Nginx neu starten
systemctl restart nginx
```

## Wichtige Verzeichnisse

- **Projekt**: `/opt/tick-guard/Stundenzettel_web/frontend`
- **Build-Output**: `/opt/tick-guard/Stundenzettel_web/frontend/build`
- **Web-Root**: `/var/www/tick-guard`
- **Nginx-Config**: `/etc/nginx/sites-available/tick-guard`

