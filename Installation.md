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
sudo apt-get update && sudo apt-get install
```

### InfluxDB
#### InfluxData Repository hinzufügen
```bash
wget -qO- https://repos.influxdata.com/influxdb.key | gpg --dearmor > /etc/apt/trusted.gpg.d/influxdb.gpg
export DISTRIB_ID=$(lsb_release -si); export DISTRIB_CODENAME=$(lsb_release -sc)
echo "deb [signed-by=/etc/apt/trusted.gpg.d/influxdb.gpg] https://repos.influxdata.com/${DISTRIB_ID,,} ${DISTRIB_CODENAME} stable" > /etc/apt/sources.list.d/influxdb.list
```

#### InfluxDB service installieren
```bash
sudo apt-get install influxdb
sudo systemctl unmask influxdb.service
sudo systemctl start influxdb
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


#upgrade pip
/usr/bin/python -m pip install --upgrade pip
```

### Wettermonitor installieren
```bash
git clone https://github.com/etiiiR/FHNW_Wettermonitor.git
cd FHNW_Wettermonitor
# Funktioniert auf Debian nicht: /usr/bin/python3 -m pip install -r requirements.txt

sudo apt-get install python3-pandas
sudo apt-get install python3-influxdb




sudo apt-get install libatlas-base-dev

sudo apt-get upgrade python3


```

### Wettermonitor automatisch starten
```bash
# 1. main.py ausführen
# 2. chrome im kiosk mode öffnen
# überprüfen, dass influx sicher zuerst gestartet wird.
# vielleicht als service installieren: https://medium.com/codex/setup-a-python-script-as-a-service-through-systemctl-systemd-f0cc55a42267

/usr/bin/python weather_app/main.py

```

```bash
```
