
# Log anzeigen
```bash
journalctl -u service-name -f
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
