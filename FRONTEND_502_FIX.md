# Frontend 502-Fehler beheben

## Problem
Nach einem Frontend-Rebuild tritt ein 502-Fehler beim Login auf.

## Ursachen

### 1. Falsche Umgebungsvariable beim Build
**Problem**: Das Frontend verwendet `VITE_API_BASE_URL`, aber das Update-Script verwendete `REACT_APP_BACKEND_URL`.

**Lösung**: 
- Scripts wurden korrigiert, verwenden jetzt `VITE_API_BASE_URL`
- Frontend neu bauen mit korrekter Umgebungsvariable

### 2. Nginx-Proxy kann Backend nicht erreichen
**Problem**: Nginx kann das Backend nicht erreichen (Backend läuft nicht oder Netzwerkproblem).

**Prüfung**:
```bash
# Prüfe ob Backend läuft
curl http://192.168.178.157:8000/health

# Prüfe Nginx-Konfiguration
nginx -t

# Prüfe Nginx-Logs
tail -f /var/log/nginx/error.log
```

**Lösung**:
- Backend starten: `systemctl start tick-guard-backend`
- Nginx-Konfiguration prüfen: `/etc/nginx/snippets/tick-guard-common.conf`
- Backend-IP prüfen: `BACKEND_HOST` sollte `192.168.178.157` sein

### 3. Frontend verwendet falsche API-URL
**Problem**: Frontend wurde mit falscher `VITE_API_BASE_URL` gebaut.

**Lösung**:
```bash
cd /opt/tick-guard/Stundenzettel_web/frontend

# Option 1: Relative /api-Routen verwenden (erfordert Nginx-Proxy)
rm -f .env.production
npm run build

# Option 2: Direkte Backend-URL verwenden
echo "VITE_API_BASE_URL=http://192.168.178.157:8000/api" > .env.production
npm run build

# Build deployen
rsync -a --delete build/ /var/www/tick-guard/
chown -R www-data:www-data /var/www/tick-guard
systemctl reload nginx
```

## Schnelle Lösung

1. **Backend prüfen**:
```bash
# Auf Backend-CT (192.168.178.157)
systemctl status tick-guard-backend
curl http://localhost:8000/health
```

2. **Frontend neu bauen** (auf Frontend-CT):
```bash
cd /opt/tick-guard/Stundenzettel_web/frontend

# .env.production entfernen (verwendet relative /api-Routen)
rm -f .env.production

# Neu bauen
npm run build

# Deployen
rsync -a --delete build/ /var/www/tick-guard/
chown -R www-data:www-data /var/www/tick-guard
systemctl reload nginx
```

3. **Nginx-Konfiguration prüfen**:
```bash
# Prüfe ob Proxy korrekt konfiguriert ist
cat /etc/nginx/snippets/tick-guard-common.conf

# Sollte enthalten:
# location /api/ {
#     proxy_pass http://192.168.178.157:8000/api/;
#     ...
# }
```

4. **Nginx-Logs prüfen**:
```bash
tail -f /var/log/nginx/error.log
# Suche nach "502" oder "upstream" Fehlern
```

## Verwendung des Update-Scripts

Das `update_frontend.sh` Script wurde korrigiert und verwendet jetzt `VITE_API_BASE_URL`:

```bash
cd /opt/tick-guard/Stundenzettel_web/scripts
bash update_frontend.sh
```

Falls Sie eine direkte Backend-URL verwenden möchten (ohne Nginx-Proxy):
```bash
PUBLIC_BACKEND_URL=http://192.168.178.157:8000/api bash update_frontend.sh
```

## Nginx-Proxy-Konfiguration

Die Nginx-Konfiguration sollte folgendes enthalten:

```nginx
location /api/ {
    proxy_pass http://192.168.178.157:8000/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_buffering off;
}
```

## Debugging

1. **Browser-Konsole prüfen**: Welche URL wird aufgerufen?
2. **Network-Tab prüfen**: Welcher Status-Code wird zurückgegeben?
3. **Backend-Logs prüfen**: Kommen Anfragen an?
4. **Nginx-Logs prüfen**: Werden Anfragen weitergeleitet?

