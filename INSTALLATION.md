# Installation
Dieses Dokument bietet eine Anleitung wie auf einem neuen Raspberry PI der Wettermonitor in Betrieb genommen werden kann.


Die Anleitung wurde mit folgender Hardware/Software getestet:
 - Raspberry PI 4 Model B
 - 32 GB Micro SD-Karte 
 - Waveshare Display 10.1
 - Raspberry Pi OS Full (32-bit) Released: 2021-05-07 Kernel version: 5.10


## Voraussetzung
 - Raspberry PI mit Touchdisplay und installiertem Raspian OS (Anleitung gibt es [hier](https://www.raspberrypi.com/documentation/computers/getting-started.html#using-raspberry-pi-imager))
 - Internetverbindung
 - Strom
 - Tastatur (eine Maus ist optional, da sie ein Touchdisplay haben)


## Erster Start
1. Dem Willkommensdialog folgen
   1. Legen Sie ein sicheres Passwort fest, notieren Sie dieses
   2. Verbinden Sie den Raspberry PI via WLAN oder Ethernet
   3. Aktualisieren Sie die Software im Willkommensdialog (dauert einige Minuten)
2. Neustarten

## Software insallieren
### Software aktualisieren
```bash
sudo apt-get purge wolfram-engine scratch scratch2 nuscratch sonic-pi idle3 -y
sudo apt-get purge smartsim java-common minecraft-pi libreoffice* -y
# TODO java-common kann nicht entfernt werden

sudo apt-get clean
sudo apt-get autoremove -y

sudo apt-get update
sudo apt-get upgrade
sudo apt-get install
```

### InfluxDB
```bash
sudo apt-get install influxdb
sudo systemctl unmask influxdb.service
sudo systemctl start influxdb

sudo apt install influxdb-client
```

### Python
```bash
sudo apt-get update
sudo apt-get install -y build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev

wget https://www.python.org/ftp/python/3.8.8/Python-3.8.8.tar.xz
tar xf Python-3.8.8.tar.xz
cd Python-3.8.8
./configure --enable-optimizations --prefix=/usr
make

sudo make altinstall

cd ..
sudo rm -r Python-3.8.8
rm Python-3.8.8.tar.xz
. ~/.bashrc

sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.8 1

/usr/bin/python -m pip install --upgrade pip

sudo pip install influxdb
sudo pip install pandas
```

### Wettermonitor installieren
```bash
git clone https://github.com/etiiiR/FHNW_Wettermonitor.git
cd FHNW_Wettermonitor
pip install -r weather_app/requirements.txt
```

### Wettermonitor initialisieren
TODO remove
```bash
python weather_app/main.py
```

### Wettermonitor automatisch starten
```bash
sudo apt-get install xdotool unclutter sed

# sudo raspi-config make sure desktop autologin is set.

cp kiosk.service /lib/systemd/system/kiosk.service
sudo systemctl enable kiosk.service
sudo systemctl start kiosk.service
# sudo systemctl status kiosk.service


# See: https://pimylifeup.com/raspberry-pi-kiosk/ but the service should wait for FHNW-Wettermonitor-Server

# add this: https://medium.com/@benmorel/creating-a-linux-service-with-systemd-611b5c8b91d6

# 1. main.py ausführen
# 2. chrome im kiosk mode öffnen
# überprüfen, dass influx sicher zuerst gestartet wird.
# vielleicht als service installieren: https://medium.com/codex/setup-a-python-script-as-a-service-through-systemctl-systemd-f0cc55a42267


```
