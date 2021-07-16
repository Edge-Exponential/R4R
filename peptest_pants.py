import RPi.GPIO as GPIO
import time
import datetime
import sys
  
#***********************************VARIABLE DECLARATIONS***********************************

#***************************************MOTOR SET UP****************************************

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

#GPIO.setup(11 , GPIO.IN, pull_up_down=GPIO.PUD_UP) #limit switch
GPIO.setup(12,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(11,  GPIO.OUT) #tableturn clk+
GPIO.setup(15, GPIO.OUT) #tableturn dir
GPIO.setup(13, GPIO.OUT) #tableturn clk-

GPIO.setup(33, GPIO.OUT) #tabletran clk+
GPIO.setup(29, GPIO.OUT) #tabletran dir
GPIO.setup(31, GPIO.OUT) #tabletran clk-

#make the blade chill out
GPIO.setup(35,GPIO.OUT)
GPIO.output(35,GPIO.LOW)
GPIO.setup(36,GPIO.OUT)
GPIO.output(36,GPIO.LOW)
GPIO.setup(37, GPIO.OUT)
GPIO.setup(38,GPIO.OUT)
GPIO.output(38, GPIO.HIGH)
GPIO.output(37, GPIO.HIGH)
#*******************************Arrays************#
Large=[19,16,13,8,4]
Medium=[16,11,6,1]
Small=[15,10,5]
Indiv=[8,4,1]

global Tstart
global Tstop
global n_pep
global blade_speed
n_pep=0
Tstart=0
Tstop=0
blade_speed=150
#########################################Rotary Interrupt########################################
global counter
global revolutions

def rotations(self):
    global n_pep
    global blade_speed
    global Tstart
    global Tstop
    n_pep=n_pep+1
    print(n_pep)
    Tstart=Tstop
    Tstop=time.time()
    deltaT=Tstop-Tstart
    print(deltaT)
    blade_speed=60/deltaT
    
            
#Interrupt that triggers on the falling edge of when a magnet is sensed and calls the prog rotations
GPIO.add_event_detect(12,GPIO.FALLING,callback=rotations,bouncetime=300)

#******************************************FUNCTIONS******************************************
        
class blade:
    def init():
        global bladeclk
        bladeclk=GPIO.PWM(35,500) #Define Pin 7, 500Hz
        bladeclk.start(0) #Stop the blade
    
    def turn(speed=0):
        global bladeclk
        bladeclk.ChangeDutyCycle(speed) #Change the duty cycle of blade motor to user input
        
    def stop():
        blade.turn(0) #Stop the blade from spinning
        
    def end():
        bladeclk.stop()   

class table:
    def init(pin1=11,pin2=33):
        global turnclk
        turnclk=GPIO.PWM(pin1,500)
        turnclk.start(0)
        
        global tranclk
        tranclk=GPIO.PWM(pin2,1000)
        tranclk.start(0)
        
    def move(dist,freq=50000,pin3=33): #Distance in inches that the table should move
        if dist>0:
            GPIO.output(29,0)
        else:
            GPIO.output(29,1)
            
        global REV
        REV=abs(dist)*200*16/(3.1415926536*.40098425196) #(.411in) Convert distance to steps on motor
        REV=round(REV)
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
        GPIO.output(15,0)
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
    blade.stop()
    
def calc(num_pep):
    global T_freq
    global blade_speed
    steps=200
    micro=16
    total_steps=steps*micro
    step_angle=360/total_steps
    pps=blade_speed/60 #Pep per sec
    
    T_rpm=60/(num_pep/pps)
    T_freq=T_rpm/((step_angle/360)*60) #Frequency to run table
    print(T_freq)
    
def advance(pep_need):
    global T_freq
    global n_pep
    while n_pep<pep_need:
        calc(pep_need)
        table.turn(T_freq)
#########################################INITIALIZE################################
blade.init()
table.init()
 #########################################Home Interrupt########################################

#switch sensor callback
# def detect(channel):
#     if GPIO.input(11)==1: #Table home
#         stop() #Stop the rotation and translation of the table
# 
# GPIO.add_event_detect(11,GPIO.RISING, callback=detect,bouncetime=100)
########################################DEMO########################################
def demo(size=14,speed=50):#speedmod coefficient to change speed of the whole script?
    
    if size==14:
        table.move(4.7)
        time.sleep(1)
        blade.turn(speed)
        table.turn(2026.133) #Turn pizza at 37.99rpm
        time.sleep(1.6) #Wait 1.6s for full rotation 4[pep]/4[pep/s]
        blade.stop()
        table.stop()
        
        table.move(-1.3)
        blade.turn(speed)
        table.turn(1013.333) #Turn the table at 19 rpm (1rpm=27Hz)
        time.sleep(3.1578) #Wait 3.1578s for full rotation 8[pep]/4[pep/s]
        blade.stop()
        table.stop()
    
        table.move(-1.3)
        blade.turn(speed)
        table.turn(623.573) #Turn table at 11.692rpm
        time.sleep(5.132)#Wait 5.132s for full rotation 13[pep]/4[pep/s]
        blade.stop()
        table.stop()
        
        table.move(-1.3)
        blade.turn(speed)
        table.turn(506.61) #Turn table at 9.499rpm
        time.sleep(6.316)#Wait 6.316s for full rotation 16[pep]/4[pep/s]
        blade.stop()
        table.stop()
        
        blade.turn(speed)#Turn blade at 2500rpm
        table.turn(426.667) #Turn table at 8rpm
        time.sleep(7.5)#Wait 7.5s for full rotation 19[pep]/4[pep/s]
        blade.stop()
        table.stop()
    
        table.move(-.3)
        
    elif size==12:
        blade.turn(speed)#Turn blade at 2500rpm
        table.turn(500) #Turn table at 9.375rpm
        time.sleep(6.4)#Wait 6.4s for full rotation 16pep]/4[pep/s]
        blade.stop()
        table.stop()
    
        table.move(1.6)
        blade.turn(speed)
        table.turn(727.2727) #Turn table at 13.636rpm
        time.sleep(4.4)#Wait 4.4s for full rotation 16[pep]/4[pep/s]
        blade.stop()
        table.stop()
    
        table.move(1.75)
        blade.turn(speed)
        table.turn(1333.333) #Turn table at 25rpm
        time.sleep(2.4) #Wait 2.4s for full rotation 13[pep]/4[pep/s]
        blade.stop()
        table.stop()
    
        table.move(2)
        blade.turn(speed)
        table.turn(0) #Turn the table at 0 rpm (1rpm=27Hz)
        time.sleep(.4) #Wait 0.4s for full rotation 8[pep]/4[pep/s]
        blade.stop()
        table.stop()
    
        table.move(-5.35)
        
    elif size==10:
        
        table.move(4.25)     
        blade.turn(speed)
        table.turn(1600) #Turn table at 30 rpm for 5 pep
        time.sleep(2) #Wait for 2s to get 5 pep
        blade.stop()
        table.stop()
        
        table.move(-1.5)
        blade.turn(speed)
        table.turn(800)#Turn table at 800Hz for 15 RPM
        time.sleep(4) #Wait 4s for 10 pep
        blade.stop()
        table.stop()
        
        table.move(-1.6)
        blade.turn(speed)
        table.turn(533.3333) #Turn table at 533.33Hz for 10 rpm
        time.sleep(6) #Wait 6s for 15 pep
        blade.stop()
        table.stop()
        
    elif size==7:
        
        table.move(5.5)
        
        blade.turn(speed)
        time.sleep(.4) #Wait 0.4s for 1pep
        blade.stop()
        
        table.move(-1.5)
        blade.turn(speed)
        table.turn(2000) #Turn table at 2000Hz for 37.5 rpm
        time.sleep(1.6) #Wait 1.6s for 4 pep
        blade.stop()
        table.stop()
        
        table.move(-1.35)
        blade.turn(speed)
        table.turn(1000) #Turn table at 1000Hz for 18.75rpm
        time.sleep(3.2) #Wait 3.2s for 8 pep
        blade.stop()
        table.stop()
        
        table.move(-2.65) #Move table to home
        
    
def demo2(size=14,speed=50):#speedmod coefficient to change speed of the whole script?
    
    if size==14:
        table.move(4.7)
        time.sleep(1)
        blade.turn(speed)
        table.turn(2026.133)
        #table.turn(T_freq) #Turn pizza at 37.99rpm, 2026.133Hz
        advance(Large[0]) #Wait 1.6s for full rotation 4[pep]/4[pep/s]
        
        table.move(-1.3)
        n_pep=0
        #table.turn(1013.333) #Turn the table at 19 rpm (1rpm=27Hz)
        #time.sleep(3.1578) #Wait 3.1578s for full rotation 8[pep]/4[pep/s]
        advance(Large[1])    
    
        table.move(-1.3)
        blade.turn(speed)
        n_pep=0
        #table.turn(623.573) #Turn table at 11.692rpm
        #time.sleep(5.132)#Wait 5.132s for full rotation 13[pep]/4[pep/s]
        advance(Large[2])
        
        table.move(-1.3)
        n_pep=0
        #table.turn(506.61) #Turn table at 9.499rpm
        #time.sleep(6.316)#Wait 6.316s for full rotation 16[pep]/4[pep/s]
        advance(Large[3])

        table.move(-1.3)
        n_pep=0
        #blade.turn(speed)#Turn blade at 2500rpm
        #table.turn(426.667) #Turn table at 8rpm
        #time.sleep(7.5)#Wait 7.5s for full rotation 19[pep]/4[pep/s]
        advance(Large[4])
        blade.stop()
        table.stop()
    
        table.move(-.3)
        