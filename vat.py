#!/usr/bin/env python3
#Alle benodigde imports
import cgitb ; cgitb.enable()
import spidev
import time
import mysql.connector
import sys
import urllib.request
import RPi.GPIO as GPIO
import signal
import settings

#Variabele maken van settings.py
ip = settings.ip
database = settings.database
login = settings.login
password = settings.password

#Vat_id meegrekregen van main.py
vat = sys.argv[1]

#SPI poort meegekregen van main.py
spi = sys.argv[2]
spi.split(",")
pin = int(spi[0])
ce = int(spi[2])

#variabele/ GPIO configuratie voor relais
warm = sys.argv[3]
koud = sys.argv[4]
warmer = int(warm)
kouder = int(koud)
GPIO.setmode(GPIO.BCM)
GPIO.setup(warmer, GPIO.OUT)
GPIO.setup(kouder, GPIO.OUT)


#Configuratie voor SPI te laten werken
spi = spidev.SpiDev() # Maak SPI object
spi.open(pin,ce) # Open SPI poort op basis van meegekregen variabele
spi.max_speed_hz = 5000 # Zet een refresh rate

# Lees de SPI poort uit voor data
def readadc(adcnum):
	if ((adcnum > 7) or (adcnum < 0)):
		return -1
	r = spi.xfer2([1,(8+adcnum)<<4,0])
	time.sleep(0.000005)
	adcout = ((r[1]&3) << 8) + r[2]
	return adcout

# Als het script wordt afgesloten wordt dit nog uitgevoerd
def terminateProcess(signalNumber, frame):
	GPIO.cleanup()
	sys.exit()


#gebruikerID opvragen van een specifiek logboek op te kijken wie de toezichthouder is
def request_toezichthouderdata():
	cnx1 = mysql.connector.connect(user=login,password=password,host=ip,database=database)
	mycur1 = cnx1.cursor()
	get_gebruiker = "SELECT Logboek.gebruiker_id FROM Logboek WHERE Logboek.vat_id = " + vat
	mycur1.execute(get_gebruiker)
	toezichthouderrequest = mycur1.fetchone()
	return toezichthouderrequest

#sensoren per vat ophalen
def request_sensordata():
	cnx2 = mysql.connector.connect(user=login,password=password,host=ip,database=database)
	mycur2 = cnx2.cursor()

	get_sensortype = "SELECT Sensor.sensor_id, Sensortype.naam, Sensortype.kommagetal FROM Sensor LEFT JOIN Sensortype ON Sensor.sensor_type_id=Sensortype.sensor_type_id WHERE Sensor.vat_id =" + vat + " AND beschikbaar = 1"
	mycur2.execute(get_sensortype)
	sensordatarequest = mycur2.fetchall()
	return sensordatarequest

#Alarm gegevens ophalen van de DB
def request_alarmdata():
	cnx3 = mysql.connector.connect(user=login,password=password,host=ip,database=database)
	mycur3 = cnx3.cursor()

	get_alarmtype = "SELECT Alarm.sensor_id, Alarm.alarm_id, Alarm.activatiewaarde, Alarm.groter_dan, Alarm.bevestig FROM Sensor LEFT JOIN Alarm ON Alarm.sensor_id = Sensor.sensor_id WHERE Sensor.vat_id =" + vat + " AND actief = 1"
	mycur3.execute(get_alarmtype)
	alarmdatarequest = mycur3.fetchall()
	return alarmdatarequest


#Controleren of de sensordata te warm of koud is en melding maken en relais aansturen
def check_sensordata(meetwaarde, activatiewaarde, groter_dan, naam, alarm_id, aanmaak_datum, bevestig):
	cnx4 = mysql.connector.connect(user=login,password=password,host=ip,database=database)
	mycur4 = cnx4.cursor()

	toezichthouder = request_toezichthouderdata()

	sql = "INSERT INTO Melding (boodschap, gebruiker_id, alarm_id, bevestig, aanmaak_datum) VALUES (%s, %s, %s, %s, %s)"
	sql2 = "UPDATE Alarm SET bevestig = 1 WHERE alarm_id = " + str(alarm_id)

	if naam == "co2" and meetwaarde < activatiewaarde and groter_dan == 1:
		GPIO.output(warmer, GPIO.HIGH)

	elif naam == "co2" and meetwaarde > activatiewaarde and groter_dan == 0:
		GPIO.output(kouder, GPIO.HIGH)

	elif naam == "co2" and meetwaarde > activatiewaarde and groter_dan == 1:
		GPIO.output(warmer, GPIO.LOW)

	elif naam == "co2" and meetwaarde < activatiewaarde and groter_dan == 0:
		GPIO.output(kouder, GPIO.LOW)


	if meetwaarde < activatiewaarde and groter_dan == 0 and bevestig == 0:
		boodschap = "De " + naam + " is te laag!"
		val = (boodschap, toezichthouder[0], alarm_id, 0, aanmaak_datum)
		mycur4.execute(sql, val)
		mycur4.execute(sql2)
		cnx4.commit()
		webUrl = urllib.request.urlopen('http://192.168.137.4:5001/api/Melding/nieuwemelding/' + str(alarm_id))
		webUrl.getcode()

	elif meetwaarde > activatiewaarde and groter_dan == 1 and bevestig == 0:
		boodschap = "De " + naam + " is te hoog!"
		val = (boodschap, toezichthouder[0], alarm_id, 0, aanmaak_datum)
		mycur4.execute(sql, val)
		mycur4.execute(sql2)
		cnx4.commit()
		webUrl = urllib.request.urlopen('http://192.168.137.4:5001/api/Melding/nieuwemelding/' + str(alarm_id))
		webUrl.getcode()

#sensor data doorsturen naar database
def send_sensordata(sensor_id,temperatuur,aanmaak_datum):
	cnx5 = mysql.connector.connect(user=login,password=password,host=ip,database=database)
	mycur5 = cnx5.cursor()

	sql4 = "INSERT INTO Sensor_data (sensor_id, meetwaarde, aanmaak_datum) VALUES (%s, %s, %s)"
	val = (sensor_id, temperatuur, aanmaak_datum)
	mycur5.execute(sql4, val)
	cnx5.commit()

#Roept de bovenstaande functie "TerminateProcess" aan als er een shutdown signal aankomt.
if __name__ == '__main__':
	signal.signal(signal.SIGTERM, terminateProcess)

	while True:
		#huide tijd
		aanmaak_datum = time.strftime('%Y-%m-%d %H:%M:%S')

		#sensor/ alarm gegevens opvragen voor forlus
		sensordatarequest = request_sensordata()
		alarmdatarequest = request_alarmdata()

		#elke waarde doorlopen en data ervan doorsturen
		for sensordata in sensordatarequest:
			if "temp" in str(sensordata[1]):
				temperatuur = ((readadc(4)*330)/1023)
				temperatuur = round(temperatuur, 2)
				send_sensordata(sensordata[0], temperatuur, aanmaak_datum)
				for alarmdata in alarmdatarequest:
					if sensordata[0] == alarmdata[0]:
						check_sensordata(temperatuur, alarmdata[2], alarmdata[3], sensordata[1], alarmdata[1], aanmaak_datum, alarmdata[4])

			elif "co2" in str(sensordata[1]):
				co2 = readadc(0) # read channel 0
				co2 = round(((co2/1023)*100), 2)
				send_sensordata(sensordata[0], co2, aanmaak_datum)
				for alarmdata in alarmdatarequest:
					if sensordata[0] == alarmdata[0]:
						check_sensordata(co2, alarmdata[2], alarmdata[3], sensordata[1], alarmdata[1], aanmaak_datum, alarmdata[4])

			elif "druk" in str(sensordata[1]):
				druk = readadc(1) # read channel 1
				druk = round(((druk/1023)*100)/33.33, 2)
				send_sensordata(sensordata[0], druk, aanmaak_datum)
				for alarmdata in alarmdatarequest:
					if sensordata[0] == alarmdata[0]:
						check_sensordata(druk, alarmdata[2], alarmdata[3], sensordata[1], alarmdata[1], aanmaak_datum, alarmdata[4])

			elif "ph" in str(sensordata[1]):
				ph = readadc(2) # read channel 2
				ph = round(((ph/1023)*100)/20, 2)
				send_sensordata(sensordata[0], ph, aanmaak_datum)
				for alarmdata in alarmdatarequest:
					if sensordata[0] == alarmdata[0]:
						check_sensordata(ph, alarmdata[2], alarmdata[3], sensordata[1], alarmdata[1], aanmaak_datum, alarmdata[4])

			elif "ethanol" in str(sensordata[1]):
				ethanol = readadc(3) # read channel 3
				ethanol = round(((ethanol/1023)*100)/4, 2)
				send_sensordata(sensordata[0], ethanol, aanmaak_datum)
				for alarmdata in alarmdatarequest:
					if sensordata[0] == alarmdata[0]:
						check_sensordata(ethanol, alarmdata[2], alarmdata[3], sensordata[1], alarmdata[1], aanmaak_datum, alarmdata[4])

			else:
				break

		#Wachten om de while terug opnieuw te runnen
		time.sleep(60)
