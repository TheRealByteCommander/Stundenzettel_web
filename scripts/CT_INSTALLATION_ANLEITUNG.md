# 📦 Anleitung: Repository auf Proxmox CTs installieren

## Übersicht

Die Installations-Skripte klonen das Repository automatisch. Sie müssen nur die Skripte auf die CTs bekommen und ausführen.

---

## 🚀 Methode 1: Skripte direkt von GitHub herunterladen (Empfohlen)

### Backend-CT (192.168.178.157)

```bash
# Auf dem Backend-CT (als root):
cd /tmp
curl -fsSL https://raw.githubusercontent.com/TheRealByteCommander/Stundenzettel_web/main/scripts/install_backend_ct.sh -o install_backend_ct.sh
chmod +x install_backend_ct.sh

# Installation starten:
FRONTEND_IP=192.168.178.156 \
BACKEND_IP=192.168.178.157 \
OLLAMA_IP=192.168.178.155 \
bash install_backend_ct.sh
```

### Frontend-CT (192.168.178.156)

```bash
# Auf dem Frontend-CT (als root):
cd /tmp
curl -fsSL https://raw.githubusercontent.com/TheRealByteCommander/Stundenzettel_web/main/scripts/install_frontend_ct.sh -o install_frontend_ct.sh
chmod +x install_frontend_ct.sh

# Installation starten:
FRONTEND_IP=192.168.178.156 \
BACKEND_HOST=192.168.178.157 \
bash install_frontend_ct.sh
```

---

## 🔧 Methode 2: Skripte vom Host-System kopieren (Proxmox)

### Schritt 1: Skripte auf Proxmox-Host vorbereiten

```bash
# Auf dem Proxmox-Host (wenn Repository bereits geklont):
cd /path/to/Stundenzettel_web
```

### Schritt 2: Skripte auf Backend-CT kopieren

```bash
# Auf dem Proxmox-Host:
pct push 101 scripts/install_backend_ct.sh /tmp/install_backend_ct.sh
pct exec 101 -- chmod +x /tmp/install_backend_ct.sh

# Installation starten:
pct exec 101 -- bash /tmp/install_backend_ct.sh \
  FRONTEND_IP=192.168.178.156 \
  BACKEND_IP=192.168.178.157 \
  OLLAMA_IP=192.168.178.155
```

**Hinweis:** Ersetzen Sie `101` mit der tatsächlichen CT-ID des Backend-Containers.

### Schritt 3: Skripte auf Frontend-CT kopieren

```bash
# Auf dem Proxmox-Host:
pct push 102 scripts/install_frontend_ct.sh /tmp/install_frontend_ct.sh
pct exec 102 -- chmod +x /tmp/install_frontend_ct.sh

# Installation starten:
pct exec 102 -- bash /tmp/install_frontend_ct.sh \
  FRONTEND_IP=192.168.178.156 \
  BACKEND_HOST=192.168.178.157
```

**Hinweis:** Ersetzen Sie `102` mit der tatsächlichen CT-ID des Frontend-Containers.

---

## 📋 Methode 3: Manuell per SSH/SCP

### Schritt 1: Skripte auf Backend-CT kopieren

```bash
# Vom lokalen Rechner (Windows PowerShell oder Linux):
scp scripts/install_backend_ct.sh root@192.168.178.157:/tmp/
ssh root@192.168.178.157 "chmod +x /tmp/install_backend_ct.sh"

# Installation starten:
ssh root@192.168.178.157 \
  "FRONTEND_IP=192.168.178.156 BACKEND_IP=192.168.178.157 OLLAMA_IP=192.168.178.155 bash /tmp/install_backend_ct.sh"
```

### Schritt 2: Skripte auf Frontend-CT kopieren

```bash
# Vom lokalen Rechner:
scp scripts/install_frontend_ct.sh root@192.168.178.156:/tmp/
ssh root@192.168.178.156 "chmod +x /tmp/install_frontend_ct.sh"

# Installation starten:
ssh root@192.168.178.156 \
  "FRONTEND_IP=192.168.178.156 BACKEND_HOST=192.168.178.157 bash /tmp/install_frontend_ct.sh"
```

---

## 🎯 Methode 4: Git direkt auf CTs installieren und klonen

### Backend-CT

```bash
# Auf dem Backend-CT (als root):
apt-get update -y
apt-get install -y git curl

# Repository klonen:
cd /opt
git clone https://github.com/TheRealByteCommander/Stundenzettel_web.git tick-guard
cd tick-guard/scripts

# Installation starten:
FRONTEND_IP=192.168.178.156 \
BACKEND_IP=192.168.178.157 \
OLLAMA_IP=192.168.178.155 \
bash install_backend_ct.sh
```

### Frontend-CT

```bash
# Auf dem Frontend-CT (als root):
apt-get update -y
apt-get install -y git curl

# Repository klonen:
cd /opt
git clone https://github.com/TheRealByteCommander/Stundenzettel_web.git tick-guard
cd tick-guard/scripts

# Installation starten:
FRONTEND_IP=192.168.178.156 \
BACKEND_HOST=192.168.178.157 \
bash install_frontend_ct.sh
```

---

## ⚙️ Optionale Parameter

### Backend-CT - Erweiterte Tools installieren

```bash
# Alle Prioritäts-Tools installieren:
INSTALL_PRIO1_TOOLS=true \
INSTALL_PRIO2_TOOLS=true \
INSTALL_PRIO3_TOOLS=true \
FRONTEND_IP=192.168.178.156 \
BACKEND_IP=192.168.178.157 \
OLLAMA_IP=192.168.178.155 \
bash install_backend_ct.sh
```

### Frontend-CT - TLS/HTTPS einrichten

```bash
# Mit Let's Encrypt Zertifikat:
RUN_CERTBOT=true \
CERTBOT_EMAIL=admin@ihre-domain.de \
PUBLIC_HOST=ihre-domain.de \
DDNS_DOMAIN=ihre-domain.de \
FRONTEND_IP=192.168.178.156 \
BACKEND_HOST=192.168.178.157 \
bash install_frontend_ct.sh
```

---

## ✅ Nach der Installation

### Backend-CT prüfen:

```bash
# Service-Status:
systemctl status tick-guard-backend

# Logs ansehen:
journalctl -u tick-guard-backend -f

# Health-Check:
curl http://localhost:8000/health
```

### Frontend-CT prüfen:

```bash
# Nginx-Status:
systemctl status nginx

# Frontend testen:
curl http://192.168.178.156/
```

---

## 🔍 Troubleshooting

### Problem: Skript kann nicht heruntergeladen werden

**Lösung:** Prüfen Sie die Internetverbindung des CTs:
```bash
ping -c 3 8.8.8.8
curl -I https://github.com
```

### Problem: Repository kann nicht geklont werden

**Lösung:** Prüfen Sie Git-Installation:
```bash
which git
git --version
```

### Problem: MongoDB-Installation schlägt fehl

**Lösung:** Prüfen Sie die Repository-Konfiguration:
```bash
cat /etc/apt/sources.list.d/mongodb-org-7.0.list
apt-get update
```

---

## 📝 Wichtige Hinweise

1. **Root-Rechte erforderlich:** Beide Skripte müssen als `root` ausgeführt werden
2. **Internetverbindung:** Die CTs benötigen Internetzugang für Package-Downloads
3. **Firewall:** Stellen Sie sicher, dass die notwendigen Ports geöffnet sind:
   - Backend: Port 8000 (nur für Frontend-IP)
   - Frontend: Port 80/443 (öffentlich)
4. **Ollama-Server:** Muss unter `192.168.178.155:11434` erreichbar sein

---

## 🎯 Empfohlene Reihenfolge

1. **Zuerst Backend-CT installieren** (192.168.178.157)
2. **Dann Frontend-CT installieren** (192.168.178.156)
3. **Ollama-Server prüfen** (192.168.178.155) - sollte bereits laufen

