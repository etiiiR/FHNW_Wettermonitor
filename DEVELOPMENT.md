
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
 ┣ 📂Messwerte                                                # CSV Template Files
 ┃ ┣ 📜messwerte_mythenquai_2007-2020.csv                     # Mythenquai Messwerte
 ┃ ┗ 📜messwerte_tiefenbrunnen_2007-2020.csv                  # Tiefenbrunnen Messwerte
 ┣ 📂weather_app
 ┃ ┣ 📂static                                                 # Static Files
 ┃ ┃ ┣ 📂Images                                               # Static Images
 ┃ ┃ ┃ ┣ 📂graphs
 ┃ ┃ ┃ ┣ 📂weather                                            # Static Weather Images für Website
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
 ┃ ┃ ┣ 📜metro-all.min.css                                      # Metro UI CSS
 ┃ ┃ ┣ 📜metro.min.js                                           # Metro UI JS
 ┃ ┃ ┣ 📜scripts.js
 ┃ ┃ ┣ 📜stop_server.js                                         # Script zum stoppen des Javascript Web Servers 
 ┃ ┃ ┗ 📜styles.css                                             # Stylesheet für die Website
 ┃ ┣ 📂templates                                                # Templates für die Website ref(https://flask.palletsprojects.com/en/2.0.x/tutorial/templates/)
 ┃ ┃ ┣ 📜graph.html                                             # Template für die Graphs
 ┃ ┃ ┣ 📜index.html                                             # Template für die Startseite Navigationsleiste und imports der anderen Seiten
 ┃ ┃ ┣ 📜load_data.html                                         # Template für die Daten laden auch splash screen gennant
 ┃ ┃ ┗ 📜main.html                                              # Daarstellungs Template für die Startseite
 ┃ ┣ 📜config.ini                                               # Config für die Datenbank & Webservice Url / Endpoints
 ┃ ┣ 📜getEntries.py
 ┃ ┣ 📜Logger.py
 ┃ ┣ 📜main.py
 ┃ ┣ 📜requirements.txt                                          # pip install -r requirements.txt 
 ┃ ┣ 📜test_sean.ipynb
 ┃ ┣ 📜weatherdata.py                                            # Helper Klasse für Controller
 ┃ ┣ 📜weatherimport.py                                          # Controller Schicht
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