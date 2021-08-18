import RPi.GPIO as GPIO
import serial
import time
import datetime
  
#***********************************VARIABLE DECLARATIONS***********************************
TargetWeight={
    7:.10,
    10:.22,
    12:.32,
    14:.44
    }
dW=-.1 #weight diff: actual v. target

#***************************************MOTOR SET UP****************************************
pin_tturnclk=36
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
   
def chz(size=14,adj=0):
    mask(size)
    time.sleep(1)
    table.turn(600)
    dc.go(3*size)
    scale.tare()
    chzwt=[scale.read()]
    step.turn(1000)
    while chzwt[-1]<TargetWeight[size]+adj:
        #time.sleep(.2)
        chzwt.append(scale.read())    
    step.stop()
    time.sleep(1)
    stop()
    time.sleep(.5)
    chzwt.append(scale.read())
    time.sleep(.01)
    print(chzwt[-12:-1])
    print(chzwt[-1])
    x=round(chzwt[-1]-TargetWeight[size],3)
    print(chzwt[-1],'-',TargetWeight[size],'=',x)
    return x
class table:
    def init(pin_turn=pin_tturnclk):
        global turnclk
        turnclk=GPIO.PWM(pin_turn,500)
        turnclk.start(0)
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
class scale:
    def init():
        global ser
        ser = serial.Serial()
        ser.port = "/dev/ttyUSB0"
        ser.baudrate = 9600
        ser.timeout = .1
        scaleWeight = 0
    def read():
        global ser
        scaleWeight=-.1
        if not ser.isOpen():
            ser.open()
        if ser.in_waiting > 220:
            ser.reset_input_buffer()
            print('bonk')
        while ser.in_waiting < 22:
            pass
        b = ser.read_all().decode('utf-8')
        bi=b.rfind('k')
        if b[bi-8]=="-": fac=-1
        else: fac=1
        b3 = b[bi-5:bi-1].strip()
        scaleWeight=round(float(b3)*fac*.80085,3)
        return scaleWeight
    def tare():
        global ser
        if not ser.isOpen():
            ser.open()
        ser.write(b'TK\n')
        ser.reset_input_buffer()

   
#########################################INITIALIZE################################
step.init()
GPIO.output(pin_stepdir,1)
table.init()
dc.init()
scale.init()