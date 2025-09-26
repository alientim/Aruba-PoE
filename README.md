# PoE Manager Web-App

Webbasierte Verwaltung und Monitoring von PoE-Devices und Switches.  
Die App ermöglicht:

- Anzeige von Device-Status (Online/Offline)
- Verwaltung von Devices und Switches
- Einstellung des Prüfintervalls
- Live-Log-Ansicht
- Benutzerverwaltung mit Adminrechten

---

## **Installation (nach einem frischen Clone)**

```bash
# Pakete installieren
sudo apt update
sudo apt install python3 python3-venv python3-pip nginx sqlite3 git nano

# Repo klonen
git clone https://gitea.int.eertmoed.net/WiS/Aruba-PoE.git /srv/poe_manager
cd /srv/poe_manager

# Virtuelle Umgebung erstellen
python3 -m venv venv
source venv/bin/activate

# Abhängigkeiten installieren
pip install --upgrade pip
pip install -r requirements.txt

# Datenbank initialisieren
python create_db.py

# Admin-Benutzer erstellen
python create_admin.py

# Web-App starten
python app.py --host=0.0.0.0 --port=5000
```

