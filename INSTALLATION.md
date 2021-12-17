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
3. Im Terminal `sudo raspi-config` ausführen.
   1. `1 System Options` > `Boot / Auto Login` > `Desktop Autologin` selektieren und Enter drücken.
   2. Mit "Finish" Dialog schliessen. Es ist kein Neustart notwendig.

## Installation via Script
Im Terminal folgender Befehl ausführen und warten bis Wetterdaten erscheinen (kann mehrere Stunden dauern):
```bash
curl -s https://raw.githubusercontent.com/etiiiR/FHNW_Wettermonitor/main/install.sh | bash
```

# Aktualisieren
```bash
cd ~/FHNW_Wettermonitor
git pull
```