#!/bin/bash

read MAC </sys/class/net/wlan0/address
sudo hostnamectl set-hostname "${MAC//:}"
