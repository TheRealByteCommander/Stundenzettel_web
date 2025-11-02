# 🔐 Routing zum Office-Rechner bei dynamischen IPs

## Problem

Der Office-Rechner hat keine feste IP-Adresse. Wie funktioniert das sichere Routing zu den lokal gespeicherten Dateien?

## Aktuelle Architektur

Das System verwendet **Dateisystem-Zugriff**, kein Netzwerk-API. Das bedeutet:

```
Backend → Dateisystem (LOCAL_RECEIPTS_PATH) → Dateien
```

**Wichtig:** Das Backend greift direkt auf das **Dateisystem** zu, wo es läuft.

## Lösung 1: Backend auf Office-Rechner (Empfohlen)

### ✅ Beste Lösung für DSGVO-Compliance

**Konzept:**
- Backend läuft direkt auf dem Office-Rechner
- `LOCAL_RECEIPTS_PATH` zeigt auf lokales Laufwerk (z.B. `C:/Reisekosten_Belege`)
- Keine Netzwerk-Verbindung nötig

**Vorteile:**
- ✅ Maximal sicher (kein Netzwerk-Traffic)
- ✅ DSGVO-konform (Daten bleiben lokal)
- ✅ Funktioniert ohne Netzwerk-Infrastruktur
- ✅ Keine IP-Probleme

**Konfiguration:**
```env
# backend/.env
LOCAL_RECEIPTS_PATH=C:/Reisekosten_Belege
```

**Setup:**
1. Backend auf Office-Rechner installieren
2. MongoDB lokal oder remote (über Internet)
3. Frontend läuft auf Webserver oder lokal
4. Backend-API erreichbar über Port-Weiterleitung oder VPN

## Lösung 2: Netzwerkfreigabe mit Hostname (DNS)

### Für verteilte Installation

**Konzept:**
- Office-Rechner hat Netzwerkfreigabe
- Verwenden Sie **Hostname** statt IP-Adresse
- Windows/Samba-Netzwerkfreigabe

### 2.1 Windows-Hostname (Einfachste Lösung)

**Voraussetzungen:**
- Office-Rechner und Webserver im gleichen Netzwerk
- Windows-Netzwerkfreigabe aktiviert
- Hostname bekannt

**Konfiguration:**
```env
# backend/.env
# Verwenden Sie Hostname statt IP
LOCAL_RECEIPTS_PATH=\\OFFICE-RECHNER\Reisekosten_Belege

# Oder mit NetBIOS-Name:
LOCAL_RECEIPTS_PATH=\\OFFICE-RECHNER.local\Reisekosten_Belege
```

**Setup auf Office-Rechner:**

1. **Hostname prüfen/ändern:**
   ```powershell
   # Hostname anzeigen
   hostname
   
   # Hostname ändern (falls nötig)
   # Systemsteuerung → System → Computername → Ändern
   ```

2. **Freigabe erstellen:**
   - Rechtsklick auf Ordner → "Freigeben" → "Erweiterte Freigabe"
   - Freigabename: `Reisekosten_Belege`
   - Berechtigungen: Lese- und Schreibzugriff

3. **Netzwerk-Zugriff konfigurieren:**
   - Windows Defender Firewall: Datei- und Druckerfreigabe erlauben
   - Netzwerk-Profil: Privat (nicht Öffentlich)

### 2.2 DNS-Eintrag (Für größere Umgebungen)

**Wenn Sie einen DNS-Server haben:**

1. **DNS-Eintrag erstellen:**
   - A-Record: `office-rechner` → Aktuelle IP des Office-Rechners
   - TTL: Niedrig (z.B. 60 Sekunden) für häufige Updates

2. **Konfiguration:**
   ```env
   LOCAL_RECEIPTS_PATH=\\office-rechner.local\Reisekosten_Belege
   ```

3. **DNS-Update-Script (auf Office-Rechner):**
   ```powershell
   # Script, das IP regelmäßig aktualisiert
   # Kann per Task Scheduler ausgeführt werden
   $currentIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -like "Ethernet*" -or $_.InterfaceAlias -like "Wi-Fi*"}).IPAddress
   # DNS-Update per API (z.B. bei DynDNS-Provider)
   ```

## Lösung 3: Gemapptes Netzwerklaufwerk

### Für Windows-zu-Windows Verbindung

**Konzept:**
- Netzwerkfreigabe wird als Laufwerksbuchstabe gemappt
- Backend verwendet Laufwerksbuchstaben statt UNC-Pfad

**Setup:**

1. **Auf Webserver (wo Backend läuft):**
   ```powershell
   # Netzwerklaufwerk manuell mappen
   net use Z: \\OFFICE-RECHNER\Reisekosten_Belege /persistent:yes /user:Benutzername Passwort
   ```

2. **Automatisches Mapping beim Start:**
   - Task Scheduler: Script beim Anmelden ausführen
   - Oder: Login-Script im Backend

3. **Konfiguration:**
   ```env
   LOCAL_RECEIPTS_PATH=Z:/Reisekosten_Belege
   ```

**Nachteil:** Bei Verbindungsabbruch muss Mapping erneuert werden.

## Lösung 4: VPN-Verbindung

### Für sichere Internet-Verbindung

**Konzept:**
- Office-Rechner und Webserver verbinden sich über VPN
- VPN stellt statische IP oder Hostname zur Verfügung

**Setup:**

1. **VPN-Server einrichten:**
   - Windows Server: RRAS (Routing and Remote Access)
   - OpenVPN, WireGuard, oder kommerzielle Lösung

2. **Statische VPN-IP:**
   - Office-Rechner bekommt feste VPN-IP (z.B. `10.8.0.10`)
   - Diese ändert sich nicht (auch wenn LAN-IP wechselt)

3. **Konfiguration:**
   ```env
   # Mit VPN-IP (statisch)
   LOCAL_RECEIPTS_PATH=\\10.8.0.10\Reisekosten_Belege
   ```

**Vorteile:**
- ✅ Sehr sicher (verschlüsselt)
- ✅ Funktioniert über Internet
- ✅ Statische IP im VPN-Netzwerk

## Lösung 5: Dynamic DNS (DDNS)

### Für Internet-basierte Verbindung

**Konzept:**
- Office-Rechner registriert sich bei DDNS-Provider
- Hostname zeigt immer auf aktuelle IP

**Setup:**

1. **DDNS-Provider wählen:**
   - No-IP (kostenlos)
   - Dynu (kostenlos)
   - DuckDNS (kostenlos)
   - Oder eigener DNS-Server mit API

2. **DDNS-Client installieren (auf Office-Rechner):**
   - No-IP DUC (Dynamic Update Client)
   - Oder Router-basiertes DDNS

3. **Konfiguration:**
   ```env
   # Mit DDNS-Hostname
   LOCAL_RECEIPTS_PATH=\\office-rechner.ddns.net\Reisekosten_Belege
   ```

**Wichtig:** 
- SMB über Internet ist **nicht sicher**!
- Nur verwenden mit VPN-Tunnel oder SSH-Tunnel

## Lösung 6: SSH-Tunnel (Linux/Mac)

### Für sichere Verbindung über Internet

**Konzept:**
- SSH-Tunnel zwischen Webserver und Office-Rechner
- SMB-Protokoll über SSH getunnelt

**Setup:**

1. **SSH-Server auf Office-Rechner:**
   ```bash
   # Linux/Mac
   sudo apt install openssh-server
   sudo systemctl enable ssh
   ```

2. **SSH-Tunnel erstellen:**
   ```bash
   # Auf Webserver (wo Backend läuft)
   ssh -L 445:localhost:445 user@office-rechner-ip
   ```

3. **SMB über Tunnel:**
   ```env
   LOCAL_RECEIPTS_PATH=//localhost/Reisekosten_Belege
   ```

**Für Windows:** PuTTY oder OpenSSH for Windows

## Lösung 7: Reverse Tunnel / Port-Weiterleitung

### Für NAT-Umgebungen

**Konzept:**
- Office-Rechner stellt Verbindung zum Webserver her (Reverse)
- Webserver leitet Requests an Office-Rechner weiter

**Setup mit SSH:**

```bash
# Auf Office-Rechner
ssh -R 8001:localhost:8001 user@webserver-ip

# Backend auf Office-Rechner läuft auf Port 8001
# Erreichbar vom Webserver aus über localhost:8001
```

**Dann:** Backend auf Office-Rechner, API-Endpoint für Dateien

## Empfohlene Lösung nach Szenario

### Szenario A: Office-Rechner und Webserver im gleichen LAN

**✅ Lösung 1 oder 2.1 (Hostname)**

```
LOCAL_RECEIPTS_PATH=\\OFFICE-RECHNER\Reisekosten_Belege
```

### Szenario B: Office-Rechner und Webserver getrennt (Internet)

**✅ Lösung 1 (Backend lokal) oder Lösung 4 (VPN)**

### Szenario C: Maximale Sicherheit / DSGVO

**✅ Lösung 1: Backend auf Office-Rechner**

```
Backend → Office-Rechner (lokal)
Frontend → Webserver (öffentlich)
API-Verbindung → VPN oder Reverse Tunnel
```

### Szenario D: Flexible Installation

**✅ Lösung 3 (Gemapptes Laufwerk) + Auto-Reconnect**

## Sicherheitsüberlegungen

### ⚠️ WICHTIG: SMB über Internet

**SMB (Server Message Block) ist NICHT sicher für Internet-Verbindung!**

- ❌ Nicht direkt über Internet verwenden
- ✅ Nur im lokalen Netzwerk oder über VPN/Tunnel

### 🔒 Empfohlene Sicherheitsmaßnahmen

1. **VPN verwenden** für Internet-Verbindungen
2. **Firewall-Regeln:** Nur benötigte Ports öffnen
3. **Authentifizierung:** Starke Passwörter für Freigaben
4. **Verschlüsselung:** Dateien werden automatisch verschlüsselt (DSGVO)
5. **Audit-Logging:** Alle Zugriffe werden protokolliert

## Troubleshooting

### Problem: "Network path not found"

**Lösung:**
1. Prüfen Sie Hostname/IP erreichbar:
   ```powershell
   ping OFFICE-RECHNER
   ```
2. Prüfen Sie Freigabe erreichbar:
   ```powershell
   dir \\OFFICE-RECHNER\Reisekosten_Belege
   ```
3. Firewall prüfen (Windows Defender Firewall)

### Problem: "Access denied"

**Lösung:**
1. Freigabe-Berechtigungen prüfen
2. Benutzername/Passwort korrekt?
3. Bei gemapptem Laufwerk: Mit Credentials verbinden

### Problem: Verbindung bricht ab

**Lösung:**
1. Auto-Reconnect aktivieren (bei gemapptem Laufwerk: `/persistent:yes`)
2. Keep-Alive für Verbindung konfigurieren
3. DDNS-Update prüfen (falls DDNS verwendet)

## Code-Änderungen für Auto-Reconnect

Optional: Auto-Reconnect-Funktionalität im Backend:

```python
# backend/server.py - Beispiel für Auto-Reconnect
import subprocess
import platform

def ensure_network_drive_connected(path: str):
    """Ensure network drive is connected"""
    if platform.system() == 'Windows' and path.startswith('\\\\'):
        # UNC-Pfad - kann gemapptes Laufwerk benötigen
        drive_letter = path[2:3] if ':' in path[0:3] else None
        if drive_letter:
            # Prüfen ob Laufwerk verbunden ist
            result = subprocess.run(['net', 'use'], capture_output=True, text=True)
            if drive_letter.upper() not in result.stdout:
                # Laufwerk neu verbinden
                # (Credentials aus sicherer Quelle laden)
                pass
```

## Zusammenfassung

**Für Office-Rechner ohne feste IP:**

1. **Best Solution:** Backend auf Office-Rechner laufen lassen
2. **LAN:** Windows-Hostname verwenden (`\\OFFICE-RECHNER\...`)
3. **Internet:** VPN + statische VPN-IP oder Reverse Tunnel
4. **Einfach:** Gemapptes Laufwerk mit Auto-Reconnect

**Sicherheit:**
- ✅ Immer VPN für Internet-Verbindungen
- ✅ Firewall-Regeln konfigurieren
- ✅ Starke Authentifizierung
- ✅ Automatische Verschlüsselung (bereits implementiert)

