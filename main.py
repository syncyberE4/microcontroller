#!/usr/bin/env python3
import cgitb ; cgitb.enable()
import os
import time
import mysql.connector
import socket
import settings

host = settings.ip
database = settings.database
login = settings.login
password = settings.password

def request_vatdata(whoami):
	cnx = mysql.connector.connect(user=login,password=password,host=host,database=database)
	sql = "SELECT Vat.online, Vat.vat_id, Vat.beschikbaar, Raspi_poort.poort, Raspi_poort.relaiswarm, Raspi_poort.relaiskoud FROM Vat LEFT JOIN Raspi_poort ON Raspi_poort.poort_id = Vat.poort_id WHERE Vat.raspi_id = " + str(whoami) + " AND Vat.manueel = 0"
	mycur = cnx.cursor()
	mycur.execute(sql)
	requestvatdata = mycur.fetchall()
	return requestvatdata

def check_whoami():
	hostname = socket.gethostname()
	cnx1 = mysql.connector.connect(user=login,password=password,host=host,database=database)
	sql1 = "SELECT Raspi.raspi_id FROM Raspi WHERE naam = \"" + hostname + "\""
	mycur1 = cnx1.cursor()
	mycur1.execute(sql1)
	checkwhoami = mycur1.fetchone()
	return checkwhoami

while True:

	whoami = check_whoami()
	requestvatdata = request_vatdata(whoami[0])

	for request in requestvatdata:
		vatx = "vat" + str(request[1])
		checkprocess = os.system("ps aux | grep python3 > /home/pi/output.txt")
		checkprocess = open('/home/pi/output.txt', 'r').read()

		if "0" in str(request[2]) and vatx not in str(checkprocess):
			os.system("sudo cp /home/pi/vat.py /home/pi/" + vatx + ".py ")
			os.system("python3 /home/pi/" + vatx + ".py " + str(request[1]) + " " + str(request[3]) + " " + str(request[4]) + " " + str(request[5])+" &")

		elif "1" in str(request[2]) and "0" in str(checkprocess):
			os.system("sudo rm -r /home/pi/" + vatx + ".py 2> /dev/null")
			os.system("sudo pkill -15 -f " + vatx + ".py &")

	time.sleep(30)
