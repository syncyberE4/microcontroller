#!/usr/bin/env python3
#alle benodigde imports
import cgitb ; cgitb.enable()
import os
import time
import mysql.connector
import socket
import settings

#variabelen maken uit het settings.py bestand
host = settings.ip
database = settings.database
login = settings.login
password = settings.password

#Alle benodigde data van de vaten wordt opgehaald
def request_vatdata(whoami):
	cnx = mysql.connector.connect(user=login,password=password,host=host,database=database)
	sql = "SELECT Vat.online, Vat.vat_id, Vat.beschikbaar, Raspi_poort.poort, Raspi_poort.relaiswarm, Raspi_poort.relaiskoud FROM Vat LEFT JOIN Raspi_poort ON Raspi_poort.poort_id = Vat.poort_id WHERE Vat.raspi_id = " + str(whoami) + " AND Vat.manueel = 0"
	mycur = cnx.cursor()
	mycur.execute(sql)
	requestvatdata = mycur.fetchall()
	return requestvatdata

#Controle zodat de microcontroller enkel vaten ophaalt waar hij verantwoordlijk voor is
def check_whoami():
	hostname = socket.gethostname()
	cnx1 = mysql.connector.connect(user=login,password=password,host=host,database=database)
	sql1 = "SELECT Raspi.raspi_id FROM Raspi WHERE naam = \"" + hostname + "\""
	mycur1 = cnx1.cursor()
	mycur1.execute(sql1)
	checkwhoami = mycur1.fetchone()
	return checkwhoami

while True:
	#funcites oproepen
	whoami = check_whoami()
	requestvatdata = request_vatdata(whoami[0])

	#loopje voor elk vat waar deze microcontroller verantwoordelijk voor is af te lopen
	for request in requestvatdata:
		#Huidige vat variabele
		vatx = "vat" + str(request[1])
		
		#Controle of er al een script voor het vat loopt
		checkprocess = os.system("ps aux | grep python3 > /etc/scripts/output.txt")
		checkprocess = open('/etc/scripts/output.txt', 'r').read()

		#if die bepaalt of het script mag blijven draaien of moet stoppen op basis van gegevens uit de database
		if "0" in str(request[2]) and vatx not in str(checkprocess):
			os.system("sudo cp /etc/scripts/vat.py /etc/scripts/" + vatx + ".py ")
			os.system("python3 /etc/scripts/" + vatx + ".py " + str(request[1]) + " " + str(request[3]) + " " + str(request[4]) + " " + str(request[5])+" &")

		elif "1" in str(request[2]) and "0" in str(checkprocess):
			os.system("sudo rm -r /etc/scripts/" + vatx + ".py 2> /dev/null")
			os.system("sudo pkill -15 -f " + vatx + ".py &")

	#wachttijd tot het script opnieuw mag draaien
	time.sleep(30)
