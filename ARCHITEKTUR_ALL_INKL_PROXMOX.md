# 🏗️ Architektur: Proxmox (Frontend + Backend) & GMKTec

## Überblick

Die aktuelle Referenzarchitektur verzichtet vollständig auf externes Hosting. Sämtliche Web-Komponenten laufen in zwei Proxmox-Containern, während der GMKTec evo x2 lokal das LLM bereitstellt. Externe Benutzer greifen ausschließlich über DDNS/WireGuard auf den Frontend-Container zu.

```
┌──────────────────────────────────────────────────────────────┐
│                       Proxmox Host                           │
│                                                              │
│  ┌──────────────────┐                  ┌──────────────────┐  │
│  │ Frontend-Container│                 │ Backend-Container│  │
│  │ (HTTPS Gateway)  │  HTTP intern     │ (FastAPI+Mongo)  │  │
│  │ - Nginx/Caddy    │ <──────────────► │ - Agents         │  │
│  │ - React Build    │                  │ - Storage        │  │
│  └──────┬───────────┘                  └──────────┬───────┘  │
│         │ HTTPS (DDNS/VPN)                        │          │
└─────────┼─────────────────────────────────────────┼──────────┘
          │                                         │
          ▼                                         ▼
  Externe Clients / Admins                    GMKTec evo x2
                                              (Ollama LLM)
```

- **Frontend-Container:** Liefert das gebaute React-Frontend, terminiert TLS, übernimmt Reverse-Proxy-Aufgaben und exponiert nur Port `443`.
- **Backend-Container:** Stellt REST-API, Agents, MongoDB und lokale Dateispeicherung bereit. Keine direkten eingehenden Verbindungen von außen.
- **GMKTec evo x2:** Stellt die Ollama-API im LAN oder via WireGuard bereit (Port `11434`).

---

## Komponenten im Detail

### Frontend-Container
- Nginx oder Caddy als Webserver & Reverse Proxy.
- Liefert statisches React-Build (`frontend/build`).
- Proxy-Pfad `/api/` leitet zu `backend-container:8000`.
- TLS via Let’s Encrypt oder interne PKI.
- Optionaler WireGuard-Server für administrativen Zugriff.

### Backend-Container
- FastAPI Applikation (`backend/server.py`).
- Agents (`backend/agents.py`) laufen im gleichen Prozess.
- MongoDB lokal (Standard-Port 27017 nur localhost).
- Verschlüsseltes Dateilager (`/var/tick-guard/receipts`).
- `.env` definiert `CORS_ORIGINS`, `LOCAL_RECEIPTS_PATH`, `OLLAMA_BASE_URL`.

### GMKTec evo x2
- Ollama Service (`ollama serve`) mit Llama 3.2.
- Statische IP oder DNS-Eintrag (`gmktec.lan`).
- Firewall-Regel: Nur Backend-Container darf Port `11434/tcp` erreichen.

---

## Netzwerk-Topologie

| Verbindung        | Protokoll | Quelle             | Ziel                    | Hinweise                          |
|-------------------|-----------|--------------------|-------------------------|-----------------------------------|
| Extern → Frontend | HTTPS     | Internet/VPN       | Frontend-Container:443  | DDNS, TLS, optional HSTS          |
| Frontend → Backend| HTTP      | Frontend-Container | Backend-Container:8000  | Interne Bridge/VLAN               |
| Backend → Ollama  | HTTP      | Backend-Container  | GMKTec:11434            | Nur LAN/VPN, statische Route      |
| Backend → MongoDB | Loopback  | Backend-Container  | localhost:27017         | Auth optional (SCRAM)             |

---

## CORS & Security Headers

- `CORS_ORIGINS` muss DDNS-Domain (`https://ddns.meinedomain.de`) und optionale Admin-Hosts enthalten.
- Frontend sendet API-Calls ausschließlich über den Proxy (`/api`), keine direkten Backend-DNS-Namen ins Build backen.
- Rate-Limits (`slowapi`) bleiben aktiv; ggf. `TRUSTED_HOSTS`/`FORWARDED_ALLOW_IPS` setzen, damit Proxy-Header korrekt interpretiert werden.

---

## Vorteile der lokalen Container-Architektur

- **Volle Kontrolle:** Keine Abhängigkeit von Hosting-Providern, sämtliche Ressourcen in eigener Infrastruktur.
- **Minimierte Angriffsfläche:** Nur ein Port nach außen offen, Backend/DB bleiben im LAN.
- **DSGVO-Konformität:** Speicherung sensibler Belege ausschließlich lokal.
- **Performanz:** Niedrige Latenz zwischen Backend, MongoDB und Agents.
- **Einfache Wartung:** Updates und Backups zentral auf Proxmox automatisierbar.

---

## Best Practices

1. **TLS/Certificates:** Let’s Encrypt (HTTP-01) oder DNS-01 via DDNS; alternativ interne CA bei reinem VPN-Betrieb.
2. **Firewalling:** `ufw` oder Proxmox-Firewall auf beiden Containern aktivieren. Nur erlaubte Subnetze für WireGuard/Ollama zulassen.
3. **Monitoring:** Promtail/Vector + Grafana/ELK für Logs; `systemd`-Healthchecks; `curl /health` per Cron.
4. **Backups:** `mongodump`, Tar-Archive des Receipts-Verzeichnisses, Konfigurations-Files (`/etc/nginx`, `.env`).
5. **Secrets-Management:** `.env`-Dateien nur root-lesbar, idealerweise via SOPS/Ansible Vault verteilt.

---

## Migration von All-inkl

1. Frontend-Build nicht mehr hochladen – stattdessen im Frontend-Container deployen.
2. DNS von All-inkl zu eigenem DDNS/Reverse-Proxy ändern.
3. `REACT_APP_BACKEND_URL` neu setzen (`https://ddns.meinedomain.de`), Build neu erstellen.
4. CORS und Push-Endpoint-URLs im Backend anpassen.

---

## Troubleshooting

- **Frontend zeigt leere Seite:** Proxy-Ziel prüfen (`proxy_pass`), Browser-Konsole auf CORS-Hinweise checken.
- **API nicht erreichbar:** `curl http://backend-container:8000/health` aus Frontend-Container testen; Firewall-Regeln prüfen.
- **Agents finden Ollama nicht:** `ping gmktec.lan`, `curl http://gmktec.lan:11434/api/tags`. IP in `.env` korrigieren.
- **Push-Benachrichtigungen:** VAPID-Keys neu generieren, Service Worker neu registrieren, DDNS-Domain in `manifest.json`/`sw.js` prüfen.

---

## Weiterführend

- `INSTALLATION_COMPLETE_CORRECT.md` – vollständige Schritt-für-Schritt-Anleitung.
- `backend/LLM_INTEGRATION.md` – Details zur Agenten-Orchestrierung mit Ollama.
- `OFFICE_RECHNER_ROUTING.md` – Routing-, VPN- und Dynamic-DNS-Strategien.
- `DSGVO_COMPLIANCE.md` – Datenschutzmaßnahmen und Audit-Logging.

Damit steht eine klar strukturierte, lokal betriebene Architektur zur Verfügung, die sämtliche Features erhält und gleichzeitig die Netzwerkangriffsfläche erheblich reduziert. Externe Zugriffe laufen ausschließlich über den gehärteten Frontend-Container, während Backend, Datenbank und LLM innerhalb des geschützten Proxmox-/WireGuard-Ökosystems verbleiben.

