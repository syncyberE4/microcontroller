#!/bin/bash

sudo apt-get update -y
sudo apt-get upgrade -y

git init
git clone https://github.com/syncyberE4/microcontroller.git

sudo mkdir /etc/scripts

cd ./microcontroller

sudo mv config.txt /boot/
sudo mv main.py /etc/scripts/
sudo mv main.service /lib/systemd/system/
sudo mv register.py /etc/scripts/
sudo mv register.service /lib/systemd/system/
sudo mv settings.py /etc/scripts
sudo mv vat.py /etc/scripts

sudo systemctl daemon-reload
sudo systemctl enable register.service
sudo systemctl daemon-reload
sudo systemctl enable main.service
sudo systemctl daemon-reload

sudo reboot now 
