#!/bin/bash
echo "removing unnessary packages"
sudo apt-get purge wolfram-engine scratch scratch2 nuscratch sonic-pi idle3 -y
sudo apt-get purge smartsim minecraft-pi libreoffice* -y

sudo apt-get clean
sudo apt-get autoremove -y

sudo apt-get update
sudo apt-get upgrade
sudo apt-get install




echo "installing influxdb"
sudo apt-get install influxdb
sudo systemctl unmask influxdb.service
sudo systemctl start influxdb

sudo apt install influxdb-client




echo "installing python 3.8.8"
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




echo "clonging wettermonitor"
git clone https://github.com/etiiiR/FHNW_Wettermonitor.git
cd FHNW_Wettermonitor




echo "installing python dependencies"
sudo /bin/python -m pip install influxdb
sudo /bin/python -m pip install pandas

sudo /bin/python -m pip install -r weather_app/requirements.txt




echo "installing wettermonitor as a service"
sudo apt-get install xdotool unclutter sed

echo "copy service"
sudo cp kiosk.service /lib/systemd/system/kiosk.service
echo "enable service"
sudo systemctl enable kiosk.service
echo "start service"
sudo systemctl start kiosk.service