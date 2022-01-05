
# Log anzeigen
```bash
journalctl -u kiosk.service -f
```

# Configs ändern bei Service adressen
Folgende Zeile ändern in der weather_app/config.ini

[Service]
URL = Servicename des Wetterdienstes

# Configs änderen bei der Datenbank für Produktion
Folgende Zeilen ändern in der weather_app/config.ini

[Database]
DB_Host = Ihr Hostname
username = Datenbankusername
password = Datenbankpasswort!! nicht im cleartext sondern als env variable 
DB_PORT = Ihr Datenbank port 
DB_Name = Datenbankname




# Projekt Struktur
📦FHNW_Wettermonitor
 ┣ 📂Messwerte
 ┃ ┣ 📜messwerte_mythenquai_2007-2020.csv
 ┃ ┗ 📜messwerte_tiefenbrunnen_2007-2020.csv
 ┣ 📂weather_app
 ┃ ┣ 📂static
 ┃ ┃ ┣ 📂Images
 ┃ ┃ ┃ ┣ 📂graphs
 ┃ ┃ ┃ ┣ 📂weather
 ┃ ┃ ┃ ┃ ┣ 📜arrow.png
 ┃ ┃ ┃ ┃ ┣ 📜barometer.png
 ┃ ┃ ┃ ┃ ┣ 📜humidity.png
 ┃ ┃ ┃ ┃ ┣ 📜rain.png
 ┃ ┃ ┃ ┃ ┣ 📜sea-level.png
 ┃ ┃ ┃ ┃ ┣ 📜temperature.png
 ┃ ┃ ┃ ┃ ┣ 📜water-drop.png
 ┃ ┃ ┃ ┃ ┣ 📜water-temperature.png
 ┃ ┃ ┃ ┃ ┗ 📜windy.png
 ┃ ┃ ┃ ┣ 📜generating_plot.png
 ┃ ┃ ┃ ┗ 📜loading.png
 ┃ ┃ ┣ 📜jquery-3.4.1.min.js
 ┃ ┃ ┣ 📜metro-all.min.css
 ┃ ┃ ┣ 📜metro.min.js
 ┃ ┃ ┣ 📜scripts.js
 ┃ ┃ ┣ 📜stop_server.js
 ┃ ┃ ┗ 📜styles.css
 ┃ ┣ 📂templates
 ┃ ┃ ┣ 📜graph.html
 ┃ ┃ ┣ 📜index.html
 ┃ ┃ ┣ 📜load_data.html
 ┃ ┃ ┗ 📜main.html
 ┃ ┣ 📜config.ini
 ┃ ┣ 📜getEntries.py
 ┃ ┣ 📜Logger.py
 ┃ ┣ 📜main.py
 ┃ ┣ 📜requirements.txt
 ┃ ┣ 📜test_sean.ipynb
 ┃ ┣ 📜weatherdata.py
 ┃ ┣ 📜weatherimport.py
 ┃ ┣ 📜wettermonitor.log
 ┣ 📜DEVELOPMENT.md
 ┣ 📜diagram.png
 ┣ 📜install.sh
 ┣ 📜INSTALLATION.md
 ┣ 📜kiosk.service
 ┣ 📜kiosk.sh
 ┣ 📜Powerpoint.pptx
 ┣ 📜README.md
 ┣ 📜response_time.txt
 ┣ 📜ui-sketch-1.png
 ┣ 📜ui-sketch-2.png
 ┣ 📜ui-sketch-3.png