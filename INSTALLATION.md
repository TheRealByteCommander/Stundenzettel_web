# 📋 Installationsanweisung - Schmitz Intralogistik Zeiterfassung

## 🏢 Über die Anwendung
**Zeiterfassungs-System für Schmitz Intralogistik GmbH**
- Wöchentliche Stundenzettel-Erstellung
- PDF-Generierung mit Firmen-Branding
- E-Mail-Versand an Mitarbeiter und Admin
- Admin-Panel für Benutzerverwaltung

---

## 🔧 Systemanforderungen

### **Server-Umgebung:**
- **Betriebssystem:** Linux (Ubuntu 20.04+ empfohlen) oder Windows 10+
- **RAM:** Mindestens 2GB, empfohlen 4GB
- **Speicher:** Mindestens 5GB freier Speicherplatz
- **Internetverbindung:** Für Package-Downloads und E-Mail-Versand

### **Software-Voraussetzungen:**
- **Python 3.11+**
- **Node.js 18+** und **npm/yarn**
- **MongoDB 6.0+**
- **Git**

---

## 📦 Installation

### **1. Repository herunterladen**
```bash
git clone <REPOSITORY_URL>
cd schmitz-zeiterfassung
```

### **2. Backend-Setup (Python/FastAPI)**

#### **Python Virtual Environment erstellen:**
```bash
cd backend
python3 -m venv venv

# Linux/Mac:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

#### **Python-Abhängigkeiten installieren:**
```bash
pip install -r requirements.txt
```

#### **Backend-Umgebungsvariablen konfigurieren:**
Erstellen Sie die Datei `backend/.env`:
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=schmitz_zeiterfassung
```

### **3. Frontend-Setup (React)**

#### **Frontend-Abhängigkeiten installieren:**
```bash
cd ../frontend
yarn install
# oder: npm install
```

#### **Frontend-Umgebungsvariablen konfigurieren:**
Erstellen Sie die Datei `frontend/.env`:
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

### **4. MongoDB-Setup**

#### **MongoDB installieren (Ubuntu):**
```bash
# MongoDB Repository hinzufügen
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# MongoDB installieren
sudo apt-get update
sudo apt-get install -y mongodb-org

# MongoDB starten
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### **MongoDB installieren (Windows):**
1. Laden Sie MongoDB von [mongodb.com](https://www.mongodb.com/try/download/community) herunter
2. Führen Sie den Installer aus
3. Starten Sie MongoDB als Service

#### **MongoDB installieren (Docker - Alternative):**
```bash
docker run -d --name mongodb -p 27017:27017 mongo:6.0
```

---

## 🚀 Anwendung starten

### **1. Backend starten:**
```bash
cd backend
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows

uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### **2. Frontend starten (neues Terminal):**
```bash
cd frontend
yarn start
# oder: npm start
```

### **3. Anwendung öffnen:**
Öffnen Sie Ihren Browser und gehen Sie zu: **http://localhost:3000**

---

## 👤 Erste Anmeldung

### **Standard Admin-Zugang:**
- **E-Mail:** `admin@schmitz-intralogistik.de`
- **Passwort:** `admin123`

> ⚠️ **Wichtig:** Ändern Sie das Admin-Passwort nach der ersten Anmeldung!

---

## ⚙️ Konfiguration

### **1. SMTP E-Mail-Konfiguration**
Nach der Anmeldung als Admin:

1. Gehen Sie zum **"Admin"**-Tab
2. Füllen Sie die **SMTP-Konfiguration** aus:
   - **SMTP Server:** z.B. `smtp.gmail.com`
   - **SMTP Port:** z.B. `587`
   - **SMTP Benutzername:** Ihre E-Mail-Adresse
   - **SMTP Passwort:** App-spezifisches Passwort
   - **Admin E-Mail:** E-Mail für Kopien der Stundenzettel

#### **Gmail-Beispiel:**
- **SMTP Server:** `smtp.gmail.com`
- **Port:** `587`
- **Benutzername:** `ihre-email@gmail.com`
- **Passwort:** [App-Passwort generieren](https://support.google.com/accounts/answer/185833)

#### **Outlook/Hotmail-Beispiel:**
- **SMTP Server:** `smtp-mail.outlook.com`
- **Port:** `587`
- **Benutzername:** `ihre-email@outlook.com`

### **2. Benutzer hinzufügen**
Im **Admin-Panel**:
1. **E-Mail** des Mitarbeiters eingeben
2. **Name** eingeben
3. **Passwort** vergeben
4. **"Benutzer erstellen"** klicken

---

## 📋 Benutzung

### **Für Mitarbeiter:**
1. **Anmelden** mit E-Mail/Passwort
2. **"Neuer Stundenzettel"** wählen
3. **Wochenbeginn** (Montag) auswählen
4. **Täglich Zeiten eintragen:**
   - Startzeit, Endzeit, Pause
   - Aufgaben, Kunde/Projekt, Ort
5. **"Stundenzettel erstellen"** klicken
6. **"Stundenzettel schicken"** → PDF per E-Mail erhalten

### **Für Administratoren:**
- **Alle Stundenzettel** einsehen
- **Neue Mitarbeiter** hinzufügen
- **SMTP-Einstellungen** verwalten
- **PDFs herunterladen**

---

## 🔧 Produktions-Deployment

### **1. Umgebungsvariablen für Produktion:**

**Backend `.env`:**
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=schmitz_zeiterfassung_prod
```

**Frontend `.env`:**
```env
REACT_APP_BACKEND_URL=https://ihre-domain.de
```

### **2. Build für Produktion:**
```bash
# Frontend build
cd frontend
yarn build

# Backend mit gunicorn (empfohlen für Produktion)
cd ../backend
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker server:app --bind 0.0.0.0:8001
```

### **3. Nginx-Konfiguration (empfohlen):**
```nginx
server {
    listen 80;
    server_name ihre-domain.de;

    # Frontend (React Build)
    location / {
        root /path/to/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    # Backend (FastAPI)
    location /api {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 🆘 Troubleshooting

### **Häufige Probleme:**

#### **"MongoDB Connection Failed"**
```bash
# MongoDB-Status prüfen
sudo systemctl status mongod

# MongoDB neu starten
sudo systemctl restart mongod
```

#### **"CORS Error" im Browser**
- Überprüfen Sie die `REACT_APP_BACKEND_URL` in `frontend/.env`
- Backend und Frontend URLs müssen korrekt konfiguriert sein

#### **"Permission Denied" bei Installation**
```bash
# Linux: sudo verwenden
sudo pip install -r requirements.txt

# Oder Python Virtual Environment nutzen
python -m venv venv
source venv/bin/activate
```

#### **E-Mail-Versand funktioniert nicht**
1. SMTP-Konfiguration im Admin-Panel prüfen
2. App-spezifisches Passwort für Gmail verwenden
3. Firewall-Einstellungen prüfen (Port 587/465)

#### **PDF-Download fehlt**
```bash
# ReportLab installation prüfen
pip install reportlab

# Backend neu starten
```

---

## 📞 Support

### **Technische Unterstützung:**
- **E-Mail:** `it-support@schmitz-intralogistik.de`
- **Telefon:** `+49 (0) XXXX XXXXXX`

### **Log-Dateien prüfen:**
```bash
# Backend-Logs
tail -f backend/logs/app.log

# Frontend-Logs (Browser-Konsole)
F12 → Console-Tab
```

---

## 🔄 Updates

### **Anwendung aktualisieren:**
```bash
# Code aktualisieren
git pull origin main

# Backend-Abhängigkeiten aktualisieren
cd backend
pip install -r requirements.txt

# Frontend-Abhängigkeiten aktualisieren
cd ../frontend
yarn install

# Anwendung neu starten
```

---

## 📄 Lizenz

**© 2025 Schmitz Intralogistik GmbH**
Dieses System ist ausschließlich für den internen Gebrauch der Schmitz Intralogistik GmbH bestimmt.

---

## 📋 Anhang

### **Verzeichnisstruktur:**
```
schmitz-zeiterfassung/
├── backend/
│   ├── server.py          # FastAPI Server
│   ├── requirements.txt   # Python Dependencies
│   └── .env              # Backend Configuration
├── frontend/
│   ├── src/
│   │   ├── App.js        # React Main App
│   │   └── components/   # UI Components
│   ├── package.json      # Node Dependencies
│   └── .env             # Frontend Configuration
└── INSTALLATION.md       # Diese Anleitung
```

### **Wichtige Dateien:**
- **Backend:** `server.py` - Haupt-API-Server
- **Frontend:** `src/App.js` - React-Anwendung
- **Konfiguration:** `.env`-Dateien in beiden Verzeichnissen
- **Abhängigkeiten:** `requirements.txt` und `package.json`

---

**Viel Erfolg mit Ihrem neuen Zeiterfassungs-System! 🚀**