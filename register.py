#!/usr/bin/env python3

import sys
import mysql.connector
import socket
import settings
import os

host = settings.ip
database = settings.database
login = settings.login
password = settings.password

cnx = mysql.connector.connect(user=login,password=password,host=host,database=database)
mycur = cnx.cursor()

def request_raspi(hostname):
        get_raspi = "SELECT * FROM Raspi WHERE Raspi.naam = \'" + hostname + "\'"
        mycur.execute(get_raspi)
        raspirequest = mycur.fetchone()
        if not raspirequest:
                return 0
        else:
                return raspirequest

def get_hostname_ip():
        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)
        return host_name, host_ip;


hostname, ip = get_hostname_ip()
raspirequest = request_raspi(hostname)

if raspirequest != 0:
        if ip not in raspirequest[2]:
                sql1= "UPDATE Raspi SET ip=\"" + ip + "\" WHERE raspi_id=" + str(raspirequest[0])
                mycur.execute(sql1)
                cnx.commit()
else:
        sql2= "INSERT INTO Raspi (naam, ip) VALUES (%s, %s)"
        val=(hostname, ip)
        mycur.execute(sql2, val)
        cnx.commit()
