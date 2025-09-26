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

Download:

```bash
wget -qO- --header 'Authorization:token bac659e323cdd044bc8677937fa6957833919444' https://gitea.int.eertmoed.net/WiS/Aruba-PoE/archive/latest.tar.gz | tar xvz ; bash /root/aruba-poe/install.sh ;
```


