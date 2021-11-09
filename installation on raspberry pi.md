##this document contains the installation of the influxdb and setup of the python environment on a raspberry pi 4 using the bash shell




#install influxdb + autostart (documentation: https://docs.influxdata.com/influxdb/v1.8/introduction/install/#)
wget -qO- https://repos.influxdata.com/influxdb.key | gpg --dearmor > /etc/apt/trusted.gpg.d/influxdb.gpg
export DISTRIB_ID=$(lsb_release -si); export DISTRIB_CODENAME=$(lsb_release -sc)
echo "deb [signed-by=/etc/apt/trusted.gpg.d/influxdb.gpg] https://repos.influxdata.com/${DISTRIB_ID,,} ${DISTRIB_CODENAME} stable" > /etc/apt/sources.list.d/influxdb.list

sudo apt-get update && sudo apt-get install influxdb
sudo service influxdb start

sudo apt install influxdb-client




#install python version 3.8.8 (documentation: https://itheo.tech/install-python-3-8-on-a-raspberry-pi)
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




#install packages
sudo pip install influxdb

sudo pip install pandas