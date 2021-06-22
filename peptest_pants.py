import RPi.GPIO as GPIO
import time
import datetime
import signal
import sys
  
#***********************************VARIABLE DECLARATIONS***********************************


#***************************************MOTOR SET UP****************************************

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

GPIO.setup(11 , GPIO.IN, pull_up_down=GPIO.PUD_UP) #limit switch
GPIO.setup(12,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(8,  GPIO.OUT) #tableturn clk
GPIO.setup(13, GPIO.OUT) #tabletran dir
GPIO.setup(15, GPIO.OUT) #tabletran clk
GPIO.setup(16, GPIO.OUT) #Relay 
# GPIO.setup(23, GPIO.OUT) #TB6560
GPIO.setup(35, GPIO.OUT) #DM860T dir
GPIO.setup(37, GPIO.OUT) #DM860T clk

#make the cheese shaker chill out
GPIO.setup(7,GPIO.OUT)
GPIO.output(7,GPIO.LOW)
GPIO.setup(3,GPIO.OUT)
GPIO.output(3,GPIO.LOW)





#******************************************FUNCTIONS******************************************
        

class blade:
    def init():
        global bladeclk
        bladeclk=GPIO.PWM(7,500) #Define Pin 7, 500Hz
        bladeclk.start(0) #Stop the blade
    
    def turn(speed=0):
        global bladeclk
        bladeclk.ChangeDutyCycle(speed) #Change the duty cycle of blade motor to user input
        
    def stop():
        blade.turn(0) #Stop the blade from spinning
        
    def end():
        bladeclk.stop()
        
class hopper:
    def init(pin35=35,pin37=37):
        global hopperclk
        hopperclk=GPIO.PWM(pin37,500) #Define the hopper pin and frequency
        hopperclk.start(0)
        GPIO.output(pin35,1)
                
    def rot(duty=50,freq=1000):
        global hopperclk
        if freq==0:
            hopperclk.ChangeDutyCycle(0)
        else:
            hopperclk.ChangeDutyCycle(duty)
            hopperclk.ChangeFrequency(freq)
            
    def stop():
        global hopperclk
        hopperclk.ChangeDutyCycle(0)
        

class table:
    def init(pin1=8,pin2=15):
        global turnclk
        turnclk=GPIO.PWM(pin1,500)
        turnclk.start(0)
        
        global tranclk
        tranclk=GPIO.PWM(pin2,1000)
        tranclk.start(0)
        
    def move(dist,freq=2000,pin3=15): #Distance in inches that the table should move
        if dist>0:
            GPIO.output(13,0)
        else:
            GPIO.output(13,1)
            
        global REV
        REV=abs(dist)*200*16/(3.1415926536*.411) #Convert distance to steps on motor
        REV=round(REV)
        print(REV)
        for i in range(0,REV):
            GPIO.output(pin3,1)
            time.sleep(1/(2*freq))
            GPIO.output(pin3,0)
            time.sleep(1/(2*freq))
            
    def trans(freq):
        global transclk
        if freq==0:
            tranclk.ChangeDutyCycle(0)
        else:
            tranclk.ChangeDutyCycle(50)
            tranclk.ChangeFrequency(freq)
            
    def turn(freq):
        global turnclk
        if freq==0:
            turnclk.ChangeDutyCycle(0)
        else:
            turnclk.ChangeDutyCycle(50)
            turnclk.ChangeFrequency(freq)
        
    def stop():
        global turnclk
        turnclk.ChangeDutyCycle(0)
        tranclk.ChangeDutyCycle(0)
    
def stop():
    table.stop()
    hopper.stop()
    blade.stop()

#########################################INITIALIZE################################
blade.init()
table.init()
hopper.init()
 #########################################Home Interrupt########################################

#switch sensor callback
def detect(channel):
    if GPIO.input(11)==1: #Table home
        stop() #Stop the rotation and translation of the table

GPIO.add_event_detect(11,GPIO.RISING, callback=detect,bouncetime=100)
#########################################Rotary Interrupt########################################
global counter
global revolutions

def rotations():
    while counter<6:
        if GPIO.input(rotary)==LOW: #Magnet sensed
            counter=counter+1 #Add one to the magnet counter
    if counter==6:
        revolutions=revolutions+1 #If six magnets were counted, 1 revolution has been completed
        counter=0 #Set the magnet count back to 0
        
#Interrupt that triggers on the falling edge of when a magnet is sensed and calls the prog rotations
GPIO.add_event_detect(12,GPIO.FALLING,callback=rotations,bouncetime=1)
########################################DEMO########################################
def demo(speedmod=1):#speedmod coefficient to change speed of the whole script?
    blade.turn(100)#Turn blade at 2500rpm
    time.sleep(.06)#Wait for blade to reach full speed
    
    table.move(.65)
    hopper.rot(50,648) #Turn hopper at 60rpm
    table.turn(1620) #Turn pizza at 60rpm
    time.sleep(1) #Wait for full rotation 4[pep]/4[pep/s]
    table.stop()
    hopper.stop()
    
    table.move(.65)
    hopper.rot(50,648)
    table.turn(810) #Turn the table at 30 rpm (1rpm=27Hz)
    time.sleep(2) #Wait for full rotation 8[pep]/4[pep/s]
    table.stop()
    hopper.stop()
    
    table.move(.65)
    hopper.rot(50,648)
    table.turn(498) #Turn table at 18.462rpm
    time.sleep(3.25)#Wait for full rotation 13[pep]/4[pep/s]
    table.stop()
    hopper.stop()
    
    table.move(.65)
    hopper.rot(50,648)
    table.turn(405) #Turn table at 15rpm
    time.sleep(4)#Wait for full rotation 16[pep]/4[pep/s]
    table.stop()
    hopper.stop()
    
    table.move(.65)
    hopper.rot(50,648)
    table.turn(341) #Turn table at 12.632rpm
    time.sleep(4.75)#Wait for full rotation 19[pep]/4[pep/s]
    table.stop()
    hopper.stop()
    
    table.move(-.65*4)
