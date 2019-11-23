#!/usr/bin/env python
#By jonah lefkoff 2019
import RPi.GPIO as GPIO
import time
import statistics
from time import sleep
from lidar_lite import Lidar_Lite
from firebase import firebase

lidar = Lidar_Lite()

GPIO.setmode(GPIO.BOARD)
segmentClock=11
segmentLatch=13
segmentData=15
buttonPin=12
button2Pin=18

GPIO.setup(segmentClock,GPIO.OUT)
GPIO.setup(segmentData,GPIO.OUT)
GPIO.setup(segmentLatch,GPIO.OUT)
GPIO.setup(buttonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP) #button
GPIO.setup(button2Pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) #switch

GPIO.output(segmentClock,GPIO.LOW)
GPIO.output(segmentData,GPIO.LOW)
GPIO.output(segmentLatch,GPIO.LOW)


firebase= firebase.FirebaseApplication('https://lidarspeedometer.firebaseio.com/') #init database

seconds = 1545925769.9618232
today  = time.ctime(seconds) #for database (date & time)

number=0

connected = lidar.connect(1) #connect lidar

#Takes a number and displays 2 numbers. Display absolute value (no negatives)
#look here maybe bug between value+number
def showNumber(value):
	number = abs(value) #Remove negative signs and any decimals
	x=0
	while(x<2):
		remainder=number % 10
		postNumber(remainder)
		number /= 10
		x += 1

#Latch the current segment data
	GPIO.output(segmentLatch,GPIO.LOW)
	GPIO.output(segmentLatch,GPIO.HIGH) #Register moves storage register on the rising edge of RCK

#Given a number, or - shifts it out to the display
def postNumber(number):
	a=1<<0
	b=1<<6
	c=1<<5
	d=1<<4
	e=1<<3
	f=1<<1
	g=1<<2
	dp=1<<7

	if   number == 1: segments =     b | c
	elif number == 2: segments = a | b |     d | e |     g
	elif number == 3: segments = a | b | c | d |         g
	elif number == 4: segments =     b | c |         f | g
	elif number == 5: segments = a |     c | d     | f | g
	elif number == 6: segments = a |     c | d | e | f | g
	elif number == 7: segments = a | b | c
	elif number == 8: segments = a | b | c | d | e | f | g
	elif number == 9: segments = a | b | c | d     | f | g
	elif number == 0: segments = a | b | c | d | e | f
	elif number == ' ': segments = 0
	elif number == 'c': segments = g | e | d
	elif number == '-': segments = g
	else : segments = False

#if (segments != dp):
	y=0
	while(y<8):
		GPIO.output(segmentClock,GPIO.LOW)
		GPIO.output(segmentData,segments & 1 << (7-y))
		GPIO.output(segmentClock,GPIO.HIGH)
		y += 1


connected = lidar.connect(1)
#numList = [92,86,55,78,35,94,90]
#while (number !=129378917123):
x=0
while True:
	bState = GPIO.input(button2Pin)
	b2State = GPIO.input(buttonPin)
	if b2State == True: #user ID input
		if bState == False:
			x+=1
			showNumber(x)
			sleep(0.15)
		else:
			showNumber(x)
	else:
		for y in range(5, 0, -1): #countdown
			showNumber(y)
			time.sleep(0.9)
		vel = lidar.getVelocity() #get lidar data
		dist = lidar.getDistance()
		velPos = abs(vel) #clean up data
		if velPos > 99: # ''
			velPos %= 10
		velPos *= 1.60934 #in MPH
		velPos = round(velPos)
		speedList = [velPos]
		for z in range(0, 5, 1):
			vel = lidar.getVelocity() #get lidar data
			dist = lidar.getDistance()
			velPos = abs(vel) #clean up data
			if velPos > 99: # ''
 				velPos %= 10
			velPos *= 1.60934 #in MPH
			velPos = round(velPos)
			speedList.append(velPos)

		velAvg = statistics.mean(speedList)
		velAvg = round(velAvg)
		showNumber(velAvg) #print to display
		firebase.post('/data', { "Distance":str(dist), "velocity":str(velAvg), "User ID":x, "Date":today}) #post to database
		time.sleep(2)
GPIO.cleanup()
