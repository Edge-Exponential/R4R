import RPi.GPIO as GPIO
import time
import threading
import stepper
import numpy as np
#import matplotlib.pyplot as plt


#***************************************SETUP****************************************

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(18 , GPIO.IN, pull_up_down=GPIO.PUD_UP) #limit switch
GPIO.setup(12,GPIO.IN,pull_up_down=GPIO.PUD_UP) #hall effect encoder
GPIO.setup(16,GPIO.OUT) #encoder debug led

tturn=stepper.motor(11,15)
ttran=stepper.motor(33,29)

#make the blade chill out
GPIO.setup(35,GPIO.OUT) #DC RPWM
GPIO.setup(36,GPIO.OUT) #DC LPWM
GPIO.setup(37,GPIO.OUT) #DC REN
GPIO.setup(38,GPIO.OUT) #DC LEN
GPIO.output(36,GPIO.LOW)
GPIO.output(35,GPIO.LOW)
GPIO.output(37,GPIO.HIGH)
GPIO.output(38,GPIO.HIGH)

#***********************Variable Declaration******************************#
npep=0 #Initialize pep cut
blade_speed=[0] #Initialize blade speed
state=1 #Initialize the state variable for cancelling
Tstart=time.time()
Tstop=time.time()

R4R={}
FULL={}
FINISH={}

R4R[14]=[0,8,12,26,34,40] #2*np.array([20,17,13,6,4]) #R4R Large
FULL[14]=[8,12,36,40,54,66] #2*np.array([33,27,20,18,6,1]) #Full Large
FINISH[14]=[0,4,24,14,20,26] #2*np.array([13,10,7,12,2]) #40 on 60 Large

R4R[12]=[2,2,12,22,32] #2*np.array([16,11,6,1]) #R4R Medium
FULL[12]=[2,16,30,42,56] #2*np.array([28,21,15,8,1]) #Full Medium
FINISH[12]=[0,14,18,20,24] #2*np.array([12,10,9,7]) #Medium R4R->Full

R4R[10]=[0,10,20,30] #2*np.array([15,10,5]) #R4R Small
FULL[10]=[6,18,32,44] #2*np.array([22,16,9,3]) #Full Small
FINISH[10]=[0,8,12,14] #2*np.array([7,6,4]) #Small R4R->Full
                  
R4R[7]=[2,8,16] #2*np.array([8,4,1]) #R4R Individual
FULL[7]=[2,14,24] #2*np.array([12,7,1]) #Individual Small
FINISH[7]=[0,3,4] #2*np.array([4,3]) #Individual R4R->Full
    
NPEP={'R4R':R4R,'FULL':FULL,'FINISH':FINISH}

#***********************Rotary Interrupt******************************#
#Detects magnet indicating half rotation; Calculates blade speed
def rotations(self):
    global npep
    global blade_speed
    global Tstart
    global Tstop
    led=GPIO.input(16)
    
    
    Tstart=Tstop
    Tstop=time.time()
    deltaT=Tstop-Tstart
    if deltaT<.085:
        return
    GPIO.output(16,not led)
    npep=npep+1 #Advance number of detections by 1
    blade_speed.append(30/deltaT) #rpm
    #print(npep,'@ ',int(blade_speed[-1]),'rpm')
    
#Interrupt that triggers on the falling edge of when a magnet is sensed and calls the prog rotations
GPIO.add_event_detect(12,GPIO.FALLING,callback=rotations,bouncetime=70)

#***********************Primary Functions******************************#
        
class blade:
    def init():
        global bladeclk
        bladeclk=GPIO.PWM(36,500) #Define Pin 36, 500Hz
        bladeclk.start(0) #Stop the blade
                  
    def turn(speed=0):
        global bladeclk
        bladeclk.ChangeDutyCycle(speed) #Change the duty cycle of blade motor to user input
        
    def const(target=0):
        p=0.01
        i=0.006
        d=0.005
        global Tstart
        global Tstop
        Tstart=time.time()
        Tstop=time.time()
        global blade_speed
        global state
        global npep
        blade_speed=[0]
        duty=0
        err=[0,0,0,0]
        while state==0:
            err[0]=err[1]
            err[1]=blade_speed[-1]-target
            err[2]=(err[1]+err[0])
            err[3]=(err[1]-err[0])
            duty=round(duty-(p*err[1]+i*err[2]+d*err[3]),2)
            if time.time()-Tstart>1:
                duty=40
            if duty>100:duty=100
            if duty<5:
                duty=5
            blade.turn(duty)
            print(duty,'%\t| ',int(blade_speed[-1]),'rpm\t| ',err[1])
            time.sleep(0.2)
    
    def stop():
        blade.turn(0) #Stop the blade from spinning
        
    def end():
        bladeclk.stop()
blade.init()

def stop():
    blade.stop()
    tturn.stop()
    ttran.stop()
def home():
    while GPIO.input(18)==1:
        ttran.step(1,50000)
    ttran.stop()
def detect(channel):
    if GPIO.input(18)==0: #Table is home
        ttran.stop() #Stop the rotation and translation of the table
GPIO.add_event_detect(18,GPIO.FALLING, callback=detect,bouncetime=100)
    
#***********************Pizza Programs******************************#   
def main(size=14,mode='R4R'):
    home()
    row1=threading.Thread(target=ttran.step,args=(-19000,50000,))
    row1.start()
    for i in range(300):
        tturn.turn(-i*10)
        time.sleep(.01)
    row1.join()
    time.sleep(.2)
    global Tstart
    global Tstop
    Tstart=time.time()
    Tstop=time.time()
    global npep
    npep=0
    global state
    state=0
    BladeTargetSpeed=150 #ideal cut speed in rpm
    
    pepcut=threading.Thread(target=blade.const,args=(BladeTargetSpeed,))
    pepcut.start()
    
    for row in NPEP[mode][size]:
        try: TableTargetSpeed=3200*BladeTargetSpeed/(60*row)*2
        except ZeroDivisionError:
            ttran.step(3302,50000)
            npep=0
            continue
        if TableTargetSpeed>3000: TableTargetSpeed=3000
        tturn.turn(-TableTargetSpeed)
        #time.sleep(60*row/BladeTargetSpeed)
        for i in range(int(32000/TableTargetSpeed)):
            if npep>=row:
                print('\t',row,': ',i,'/ ',int(32000/TableTargetSpeed))
                break
            time.sleep(0.1)
        ttran.step(3302,50000)
        npep=0   
    state=1
    blade.stop()
    ttran.stop()
    tturn.stop()
    home()
    stop()
    pepcut.join()
    #print('avg=',round(np.mean(blade_speed[10:-1]),3),'\tstd=',round(np.std(blade_speed[10:-1]),3))

