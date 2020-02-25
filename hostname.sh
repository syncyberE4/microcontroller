#!/bin/bash

#MAC adress van de wifi adapter opvragen
read MAC </sys/class/net/wlan0/address

#MAC adress als hostname instellen
sudo hostnamectl set-hostname "${MAC//:}"
