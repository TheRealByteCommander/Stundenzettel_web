# 📋 Schnell-Setup Guide - Schmitz Intralogistik Zeiterfassung

## 🚀 Express-Installation (5 Minuten)

### **Voraussetzungen installieren:**

**Windows:**
- Installieren Sie von den offiziellen Websites:
  - **Python:** https://www.python.org/downloads/ (Python 3.11+)
  - **Node.js:** https://nodejs.org/ (Node.js 18.x oder höher)
  - **MongoDB:** https://www.mongodb.com/try/download/community
  - **Git:** https://git-scm.com/downloads

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip nodejs npm mongodb git

# CentOS/RHEL
sudo yum install python3 python3-pip nodejs npm mongodb-org git

# macOS (mit Homebrew)
brew install python3 node mongodb-community git
```

### **1. Projekt klonen und einrichten:**

**Windows (PowerShell):**
```powershell
git clone <REPOSITORY_URL>
cd Stundenzettel_web

# Backend setup
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1  # PowerShell
# Oder: venv\Scripts\activate.bat  # CMD
pip install -r requirements.txt

# Frontend setup
cd ..\frontend
npm install -g yarn
npm install --legacy-peer-deps
```

**Linux/Mac:**
```bash
git clone <REPOSITORY_URL>
cd Stundenzettel_web

# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install -g yarn
npm install --legacy-peer-deps
```

### **2. Konfigurationsdateien erstellen:**

**Windows (PowerShell) - Backend (.env):**
```powershell
cd backend
Set-Content .env "MONGO_URL=mongodb://localhost:27017"
Add-Content .env "DB_NAME=stundenzettel"
```

**Windows (CMD) - Backend (.env):**
```cmd
cd backend
echo MONGO_URL=mongodb://localhost:27017 > .env
echo DB_NAME=stundenzettel >> .env
```

**Linux/Mac - Backend (.env):**
```bash
cd backend
echo "MONGO_URL=mongodb://localhost:27017" > .env
echo "DB_NAME=stundenzettel" >> .env
```

**Frontend (.env) - Alle Plattformen:**
```powershell
# Windows PowerShell
cd ..\frontend
Set-Content .env "REACT_APP_BACKEND_URL=http://localhost:8000"
```

```bash
# Linux/Mac
cd ../frontend
echo "REACT_APP_BACKEND_URL=http://localhost:8000" > .env
```

### **3. MongoDB starten:**

**Windows:**
```powershell
# Als Administrator in PowerShell:
net start MongoDB

# Oder als Service:
Start-Service MongoDB
```

**Linux:**
```bash
sudo systemctl start mongod
```

**Mac:**
```bash
brew services start mongodb-community
```

**Docker (Alternative - Alle Plattformen):**
```powershell
# Windows PowerShell
docker run -d --name mongodb -p 27017:27017 mongo:6.0
```

```bash
# Linux/Mac
docker run -d --name mongodb -p 27017:27017 mongo:6.0
```

### **4. Anwendung starten:**

**Windows (PowerShell) - Terminal 1 (Backend):**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

**Windows (CMD) - Terminal 1 (Backend):**
```cmd
cd backend
venv\Scripts\activate
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

**Linux/Mac - Terminal 1 (Backend):**
```bash
cd backend
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 (Frontend) - Alle Plattformen:**
```powershell
# Windows PowerShell
cd frontend
npm start
```

```bash
# Linux/Mac
cd frontend
npm start
```

### **5. Erste Anmeldung:**
- **URL:** http://localhost:3000
- **Login:** admin@schmitz-intralogistik.de
- **Passwort:** admin123

---

## ⚡ Docker-Setup (noch schneller)

### **docker-compose.yml erstellen:**
```yaml
version: '3.8'
services:
  mongodb:
    image: mongo:6.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

  backend:
    build: ./backend
    ports:
      - "8001:8001"
    environment:
      - MONGO_URL=mongodb://mongodb:27017
      - DB_NAME=schmitz_zeiterfassung
    depends_on:
      - mongodb

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_BACKEND_URL=http://localhost:8001
    depends_on:
      - backend

volumes:
  mongodb_data:
```

### **Docker starten:**
```bash
docker-compose up --build
```

---

## 🔧 Erste Konfiguration

### **Nach der Anmeldung sofort erledigen:**

1. **SMTP konfigurieren** (Admin-Tab):
   ```
   Gmail-Beispiel:
   Server: smtp.gmail.com
   Port: 587
   Username: ihre-email@gmail.com
   Password: [App-Passwort]
   Admin-Email: admin@schmitz-intralogistik.de
   ```

2. **Ersten Mitarbeiter anlegen** (Admin-Tab):
   ```
   Email: mitarbeiter@schmitz-intralogistik.de
   Name: Max Mustermann
   Passwort: MitarbeiterPass123!
   ```

3. **Test-Stundenzettel erstellen:**
   - "Neuer Stundenzettel" → Woche wählen
   - Beispiel-Daten eintragen
   - PDF per E-Mail senden testen

---

## 🆘 Schnelle Fehlerbehebung

```bash
# MongoDB läuft nicht?
sudo systemctl status mongod
sudo systemctl start mongod

# Python-Fehler?
pip install --upgrade pip
pip install -r requirements.txt

# Node-Fehler?
rm -rf node_modules package-lock.json
yarn install

# Port bereits belegt?
sudo netstat -tulpn | grep :8001
sudo kill -9 <PID>
```

---

## 📱 Mobile Zugriff einrichten

**Frontend .env anpassen:**
```env
REACT_APP_BACKEND_URL=http://IHR-SERVER-IP:8001
```

**Backend für externe Zugriffe:**
```bash
uvicorn server:app --host 0.0.0.0 --port 8001
```

---

**✅ Fertig! Das Zeiterfassungs-System läuft!**

**Wichtige URLs:**
- **Anwendung:** http://localhost:3000
- **API-Dokumentation:** http://localhost:8001/docs
- **Admin-Login:** admin@schmitz-intralogistik.de / admin123