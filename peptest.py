import RPi.GPIO as GPIO
import time
import stepper
import threading
  
#***********************************VARIABLE DECLARATIONS***********************************


#***************************************MOTOR SET UP****************************************

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
lim_pin=18
GPIO.setup(lim_pin,GPIO.IN, pull_up_down=GPIO.PUD_UP) #limit switch 
pep=stepper.motor(36,35)
tturn=stepper.motor(11,15)
ttran=stepper.motor(33,29)

#******************************************FUNCTIONS******************************************
def in2step(inch):
    return int(inch*200*16/(3.1415926536*.411)) #Convert distance to steps on motor

def dem0(mod=1):#speed modifier coefficient to change speed of the whole script?
    ttran.turn(12000)
    while GPIO.input(lim_pin):pass
    ttran.stop()
    ttran.step(in2step(1.3*5),12000*mod)
    blade_speed=60*(650*mod) #Turn blade at 1rps (60rpm)
    pizza_speed=60*(30*mod) #Turn pizza at ?
    tturn.ramp(pizza_speed/4)
    pep.ramp(blade_speed)
    for peps in [4,10,16]:
        print(peps)
        tturn.turn(pizza_speed/peps) #4 pepwidth/s tangential velocity
        time.sleep(.9*peps/mod) #Full rotation: 19[pep]*60[sec/min] / 1[pep/s]
        ttran.step(-1.3,12000*mod) 
    pep.stop()
    table.stop()
    table.home()        

class pep:
    def init(freq=100,pin=36):
        global bladeclk
        global oldfreq
        oldfreq=freq
        GPIO.setup(pin,GPIO.OUT)
        bladeclk=GPIO.PWM(pin,freq)
        bladeclk.start(0)
    def turn(newfreq):
        if newfreq<1:
            newfreq=1
        global oldfreq
        global bladeclk
        bladeclk.ChangeDutyCycle(50)
        for i in range(oldfreq,newfreq,round((newfreq-oldfreq)/10)):
            bladeclk.ChangeFrequency(i)
            time.sleep(.1)
        oldfreq=newfreq    
    def rev():
        GPIO.output(35,1-GPIO.input(35))
    def stop():
        pep.turn(100)
        bladeclk.ChangeDutyCycle(0)
def demo(mod=1):#speed modifier coefficient to change speed of the whole script?
    table.move(.01)
    table.home()
    table.move(1.3*5)#position return
    blade_speed=60*(650*mod) #Turn blade at 1rps (60rpm)
    pizza_speed=60*(30*mod) #Turn pizza at ?
    for i in range(0,int(pizza_speed/4),int(pizza_speed/40)):
        table.turn(i)
        time.sleep(.1)
    time.sleep(1)
    pep.turn(blade_speed)
    for peps in [4,10,16]:
        print(peps)
        table.turn(pizza_speed/peps) #4 pepwidth/s tangential velocity
        time.sleep(.9*peps/mod) #Full rotation: 19[pep]*60[sec/min] / 1[pep/s]
        table.move(-1.3,12000*mod) 
    pep.stop()
    table.stop()
    table.home()
        
       
class table:
    def init(pin1=11,pin2=33):
        global turnclk
        GPIO.setup(pin1,GPIO.OUT)
        turnclk=GPIO.PWM(pin1,500)
        turnclk.start(0)
        global tranclk
        GPIO.setup(pin2,GPIO.OUT)
        tranclk=GPIO.PWM(pin2,1000)
        tranclk.start(0)
        
    def move(dist,freq=20000,clkpin=33,dirpin=29): #Distance in inches that the table should move
        GPIO.setup(dirpin,GPIO.OUT)
        if dist>0:
            GPIO.output(dirpin,1)
        else:
            GPIO.output(dirpin,0)
            
        global REV
        REV=abs(dist)*200*16/(3.1415926536*.411) #Convert distance to steps on motor
        REV=round(REV)
        for i in range(0,REV):
            GPIO.output(clkpin,1)
            time.sleep(1/(2*freq))
            GPIO.output(clkpin,0)
            time.sleep(1/(2*freq))
    def home(clkpin=33,dirpin=29):
        GPIO.output(dirpin,GPIO.LOW)
        tranclk.ChangeDutyCycle(50)
        tranclk.ChangeFrequency(20000)
        while GPIO.input(18):
            pass
        tranclk.ChangeDutyCycle(0)
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
def stop():
    pep.stop()
    table.stop()