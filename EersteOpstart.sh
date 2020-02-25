#!/bin/bash

#update en upgrade voor de meest recente versies
sudo apt-get update -y
sudo apt-get upgrade -y

#alle benodigde installaties uitvoeren
sudo apt-get install python3-dev python3-rpi.gpio python3-spidev -y
sudo apt-get install python-pip python3-git -y
sudo pip install wiringpi2 -y
sudo apt-get install git -y
sudo apt-get install python3-mysql.connector -y

#repository van github afhalen
git init
git clone https://github.com/syncyberE4/microcontroller.git

#map maken als plaats voor alle scripts
sudo mkdir /etc/scripts

#naar directory gaan die net van github is gehaald
cd ./microcontroller

#hostnaam aanpassen naar MAC adress
sh ./hostname.sh

#alles op de juiste plaats zetten
sudo mv config.txt /boot/
sudo mv main.py /etc/scripts/
sudo mv main.service /lib/systemd/system/
sudo mv register.py /etc/scripts/
sudo mv register.service /lib/systemd/system/
sudo mv settings.py /etc/scripts
sudo mv vat.py /etc/scripts

#alle services starten 
sudo systemctl daemon-reload
sudo systemctl enable register.service
sudo systemctl daemon-reload
sudo systemctl enable main.service
sudo systemctl daemon-reload

#systeem herstarten
sudo reboot now 
