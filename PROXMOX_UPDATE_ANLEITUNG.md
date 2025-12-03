# 🔄 Proxmox Container Update-Anleitung

## Übersicht

Diese Anleitung zeigt, wie Sie die Backend- und Frontend-Container auf Proxmox mit den neuesten Änderungen aus dem Repository aktualisieren.

---

## 🚀 Option 1: Automatisches Update (Empfohlen)

### Backend-Container aktualisieren

```bash
# 1. SSH in den Backend-Container
ssh root@192.168.178.157  # Ihre Backend-IP

# 2. In das Projekt-Verzeichnis wechseln
cd /opt/tick-guard/Stundenzettel_web

# 3. Update-Script ausführen
cd scripts
sudo ./update_backend.sh
# Oder mit vollständigem Pfad:
# sudo /opt/tick-guard/Stundenzettel_web/scripts/update_backend.sh
```

Das Script führt automatisch aus:
- ✅ Backup der `.env` Datei
- ✅ Git Pull (neueste Änderungen)
- ✅ Prüfung ob `requirements.txt` geändert wurde
- ✅ Aktualisierung der Python-Abhängigkeiten (nur bei Änderungen)
- ✅ Service-Neustart
- ✅ Health-Check

### Frontend-Container aktualisieren

```bash
# 1. SSH in den Frontend-Container
ssh root@192.168.178.156  # Ihre Frontend-IP

# 2. In das Projekt-Verzeichnis wechseln
cd /opt/tick-guard/Stundenzettel_web

# 3. Update-Script ausführen
cd scripts
sudo ./update_frontend.sh
# Oder mit vollständigem Pfad:
# sudo /opt/tick-guard/Stundenzettel_web/scripts/update_frontend.sh
```

Das Script führt automatisch aus:
- ✅ Backup von `.env.production` und Build
- ✅ Git Pull (neueste Änderungen)
- ✅ Prüfung ob `package.json` geändert wurde
- ✅ Aktualisierung der Node-Abhängigkeiten (nur bei Änderungen)
- ✅ Frontend-Build
- ✅ Deployment nach `/var/www/tick-guard`
- ✅ Nginx-Reload
- ✅ Frontend-Health-Check

---

## 🔧 Option 2: Manuelles Update

### Backend-Container (manuell)

```bash
# 1. SSH in den Backend-Container
ssh root@192.168.178.157

# 2. In das Backend-Verzeichnis wechseln
cd /opt/tick-guard/Stundenzettel_web/backend

# 3. Änderungen holen
git pull origin main

# 4. Python-Abhängigkeiten aktualisieren (falls requirements.txt geändert wurde)
source venv/bin/activate
pip install -r requirements.txt --upgrade
deactivate

# 5. Service neu starten
sudo systemctl restart tick-guard-backend

# 6. Status prüfen
sudo systemctl status tick-guard-backend
```

### Frontend-Container (manuell)

```bash
# 1. SSH in den Frontend-Container
ssh root@192.168.178.156

# 2. In das Frontend-Verzeichnis wechseln
cd /opt/tick-guard/Stundenzettel_web/frontend

# 3. Änderungen holen
git pull origin main

# 4. Node-Abhängigkeiten aktualisieren (falls package.json geändert wurde)
npm install --legacy-peer-deps

# 5. Frontend builden
npm run build

# 6. Build deployen
sudo rsync -a --delete build/ /var/www/tick-guard/
sudo chown -R www-data:www-data /var/www/tick-guard

# 7. Nginx neu laden
sudo nginx -t && sudo systemctl reload nginx
```

---

## ⚙️ Update-Script Optionen

### Backend-Update mit Optionen

```bash
# Backup überspringen
sudo SKIP_BACKUP=true ./update_backend.sh

# Abhängigkeiten immer aktualisieren (auch wenn requirements.txt unverändert)
sudo FORCE_UPDATE_DEPS=true ./update_backend.sh

# Beide Optionen kombinieren
sudo SKIP_BACKUP=true FORCE_UPDATE_DEPS=true ./update_backend.sh
```

### Frontend-Update mit Optionen

```bash
# Backup überspringen
sudo SKIP_BACKUP=true ./update_frontend.sh

# Abhängigkeiten immer aktualisieren
sudo FORCE_UPDATE_DEPS=true ./update_frontend.sh

# Build überspringen (nur Git-Pull und Dependencies)
sudo SKIP_BUILD=true ./update_frontend.sh

# Alle Optionen kombinieren
sudo SKIP_BACKUP=true FORCE_UPDATE_DEPS=true ./update_frontend.sh
```

---

## 🔍 Nach dem Update prüfen

### Backend prüfen

```bash
# Service-Status
sudo systemctl status tick-guard-backend

# Logs ansehen
sudo journalctl -u tick-guard-backend -f

# Health-Check
curl http://localhost:8000/health

# API testen
curl http://localhost:8000/api/auth/me
```

### Frontend prüfen

```bash
# Nginx-Status
sudo systemctl status nginx

# Nginx-Logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Frontend testen
curl http://localhost/
```

---

## 🐛 Troubleshooting

### Problem: Update-Script nicht gefunden

**Lösung:**
```bash
# Prüfe ob das Script existiert
ls -la /opt/tick-guard/Stundenzettel_web/scripts/update_backend.sh

# Falls nicht vorhanden, hole die neuesten Scripts
cd /opt/tick-guard/Stundenzettel_web
git pull origin main
```

### Problem: Service startet nicht nach Update

**Lösung:**
```bash
# Logs prüfen
sudo journalctl -u tick-guard-backend -n 50

# Service manuell starten
sudo systemctl start tick-guard-backend

# Prüfe .env Datei
cat /opt/tick-guard/Stundenzettel_web/backend/.env
```

### Problem: Frontend-Build fehlgeschlagen

**Lösung:**
```bash
# Node-Version prüfen (sollte 18+ sein)
node --version

# Alten Build wiederherstellen
sudo rsync -a /var/www/tick-guard.old.*/ /var/www/tick-guard/

# Oder manuell neu builden
cd /opt/tick-guard/Stundenzettel_web/frontend
npm install --legacy-peer-deps
npm run build
sudo rsync -a --delete build/ /var/www/tick-guard/
```

### Problem: Git-Pull schlägt fehl (Merge-Konflikte)

**Lösung:**
```bash
# Status prüfen
git status

# Konflikte anzeigen
git diff

# Falls nötig, Änderungen stashen
git stash

# Erneut pullen
git pull origin main

# Gestashte Änderungen wieder anwenden (falls gewünscht)
git stash pop
```

---

## 📋 Schnell-Referenz

### Backend-Update (Schnell)

```bash
ssh root@192.168.178.157
cd /opt/tick-guard/Stundenzettel_web/scripts && sudo ./update_backend.sh
```

### Frontend-Update (Schnell)

```bash
ssh root@192.168.178.156
cd /opt/tick-guard/Stundenzettel_web/scripts && sudo ./update_frontend.sh
```

### Beide Container aktualisieren

```bash
# Backend
ssh root@192.168.178.157 "cd /opt/tick-guard/Stundenzettel_web/scripts && sudo ./update_backend.sh"

# Frontend
ssh root@192.168.178.156 "cd /opt/tick-guard/Stundenzettel_web/scripts && sudo ./update_frontend.sh"
```

---

## ✅ Checkliste nach Update

- [ ] Backend-Service läuft (`systemctl status tick-guard-backend`)
- [ ] Backend-Health-Check erfolgreich (`curl http://localhost:8000/health`)
- [ ] Frontend erreichbar (`curl http://localhost/`)
- [ ] Nginx läuft (`systemctl status nginx`)
- [ ] Keine Fehler in den Logs
- [ ] Funktionen im Browser testen

---

## 🔄 Regelmäßige Updates

Für automatische Updates können Sie einen Cron-Job einrichten:

```bash
# Crontab bearbeiten
sudo crontab -e

# Beispiel: Täglich um 3 Uhr morgens Backend aktualisieren
0 3 * * * cd /opt/tick-guard/Stundenzettel_web/scripts && /bin/bash ./update_backend.sh >> /var/log/tick-guard-update.log 2>&1
```

**⚠️ Wichtig:** Automatische Updates sollten nur mit Vorsicht verwendet werden. Besser: Regelmäßig manuell updaten und vorher testen.

---

**Update erfolgreich! 🎉**

