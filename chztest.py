import RPi.GPIO as GPIO
import time
import datetime
  
#***********************************VARIABLE DECLARATIONS***********************************


#***************************************MOTOR SET UP****************************************
pin_tturnclk=36
pin_tmoveclk=29
pin_tmovedir=31
pin_noid7=16
pin_noid10=15
pin_noid12=13
pin_noid14=12
pin_stepclk=37
pin_stepdir=35
pin_dcr=11
pin_dcl=7
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

GPIO.setup(pin_tturnclk, GPIO.OUT) #tableturn clk
GPIO.setup(pin_tmovedir, GPIO.OUT) #tabletran dir
GPIO.setup(pin_tmoveclk, GPIO.OUT) #tabletran clk
GPIO.setup(pin_noid7, GPIO.OUT) #Relay for solenoid 7
GPIO.setup(pin_noid10, GPIO.OUT) #Relay for solenoid 10
GPIO.setup(pin_noid12, GPIO.OUT) #Relay for solenoid 12
GPIO.setup(pin_noid14, GPIO.OUT) #Relay for solenoid 14
GPIO.setup(pin_stepdir, GPIO.OUT) #DM860T dir
GPIO.setup(pin_stepclk, GPIO.OUT) #DM860T clk

#make the dc motor chill out
GPIO.setup(pin_dcl,GPIO.OUT)
GPIO.output(pin_dcl,GPIO.LOW)
GPIO.setup(pin_dcr,GPIO.OUT)
GPIO.output(pin_dcr,GPIO.LOW)


#******************************************FUNCTIONS******************************************
        

class step:
    def init(freq=100,pin=pin_stepclk):
        global stepclk
        global oldfreq
        oldfreq=freq
        stepclk=GPIO.PWM(pin,freq)
        stepclk.start(0)
    
    def turn(newfreq):
        if newfreq<1:
            newfreq=1
        global oldfreq
        global stepclk
        stepclk.ChangeDutyCycle(50)
        for i in range(oldfreq,newfreq,50*(2*(newfreq>oldfreq)-1)):
            stepclk.ChangeFrequency(i)
            time.sleep(.03)
        oldfreq=newfreq
        
    def rev():
        GPIO.output(35,1-GPIO.input(35))
    def stop():
        step.turn(1)
        stepclk.ChangeDutyCycle(0)
   
class chz:
    def mask(size=14,timeadj=1.08):
        mask(size)
        time.sleep(1)
        table.turn(400)
        dc.go(3.6*size)#13%DC for warm dry shred, 11 for cold wet fresh
        step.turn(1000)
        time.sleep(.9*size*size/19.6*timeadj)
        dc.go(15)
        time.sleep(.1*size*size/19.6*timeadj)
        step.stop()
        stop()
        time.sleep(1)
        dc.go(0)
        mask(0)
        
    def spiral(speed=3,feed=300,dist=1.83):
        inps=speed/6.28 #inch per second
        spsr=inps*1600 #steps per second-radius; multiply by radius for motor speed
        dc.go(20)
        step.turn(feed)
        table.turn(500)
        time.sleep(1)
        for radius in [dist,2*dist,3*dist]:
            table.move(-dist)
            table.turn(spsr/radius) #inps/circumference=rpm 
            time.sleep(radius/inps)#Wait for full rotation   
        table.stop()
        step.stop()
        dc.go(0)
        
class table:
    def init(pin_turn=pin_tturnclk,pin_move=pin_tmoveclk):
        global turnclk
        turnclk=GPIO.PWM(pin_turn,500)
        turnclk.start(0)
        global tranclk
        tranclk=GPIO.PWM(pin_move,1000)
        tranclk.start(0)
        
    def move(dist,freq=20000,pin3=38): #Distance in inches that the table should move
        if dist>0:
            GPIO.output(36,1)
        else:
            GPIO.output(36,0)
            
        global REV
        REV=abs(dist)*200*16/(3.1415926536*.411) #Convert distance to steps on motor
        REV=round(REV)
        print(REV)
        for i in range(0,REV):
            GPIO.output(pin3,1)
            time.sleep(1/(2*freq))
            GPIO.output(pin3,0)
            time.sleep(1/(2*freq))
        
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
def mask(size):
        GPIO.output(pin_noid7,size==7)
        GPIO.output(pin_noid10,size==10)
        GPIO.output(pin_noid12,size==12)
        GPIO.output(pin_noid14,size==14)
class dc:
    def init():
        global dcclk
        dcclk=GPIO.PWM(pin_dcr,500)
        dcclk.start(0)
    def go(speed=100):
        global dcclk
        dcclk.ChangeDutyCycle(speed)
   

def stop():
    dc.go(0)
    mask(0)
    step.stop()
    table.stop()
    

    
#########################################INITIALIZE################################
step.init()
GPIO.output(pin_stepdir,1)
table.init()
dc.init()