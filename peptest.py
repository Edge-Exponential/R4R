import RPi.GPIO as GPIO
import time
import datetime
  
#***********************************VARIABLE DECLARATIONS***********************************


#***************************************MOTOR SET UP****************************************

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

GPIO.setup(11 , GPIO.IN, pull_up_down=GPIO.PUD_UP) #limit switch

GPIO.setup(8,  GPIO.OUT) #tableturn clk
GPIO.setup(36, GPIO.OUT) #tabletran dir
GPIO.setup(38, GPIO.OUT) #tabletran clk
GPIO.setup(16, GPIO.OUT) #Relay 
# GPIO.setup(23, GPIO.OUT) #TB6560
GPIO.setup(35, GPIO.OUT) #DM860T dir
GPIO.setup(37, GPIO.OUT) #DM860T clk

#make the cheese dc motor chill out
GPIO.setup(7,GPIO.OUT)
GPIO.output(7,GPIO.LOW)
GPIO.setup(3,GPIO.OUT)
GPIO.output(3,GPIO.LOW)

#mag sensor callback
def sensorCallback(channel):
  # Called if sensor output changes
  timestamp = time.time()
  stamp = datetime.datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
  if GPIO.input(channel):
    # No magnet
    #print("Sensor HIGH " + stamp)
    return 0
  else:
    # Magnet
    #print("Sensor LOW " + stamp)
    return 1

#switch sensor callback
def switchCallback(channel):
  # Called if sensor output changes
  if GPIO.input(channel):

    return 0
  else:
    print("PRESSED")
    return 1


#******************************************FUNCTIONS******************************************
        

class pep:
    def init(freq=100,pin=37):
        global bladeclk
        global oldfreq
        oldfreq=freq
        bladeclk=GPIO.PWM(pin,freq)
        bladeclk.start(0)
    
    def turn(newfreq):
        if newfreq<1:
            newfreq=1
        global oldfreq
        global bladeclk
        bladeclk.ChangeDutyCycle(50)
        for i in range(oldfreq,newfreq,50*(2*(newfreq>oldfreq)-1)):
            bladeclk.ChangeFrequency(i)
            time.sleep(.03)
        oldfreq=newfreq    
    def rev():
        GPIO.output(35,1-GPIO.input(35))
    def stop():
        pep.turn(100)
        bladeclk.ChangeDutyCycle(0)
        
    def end():
        bladeclk.stop()
    def demo(mod=1):#speed modifier coefficient to change speed of the whole script?
        pep.turn(100)#Turn blade at 60rpm
    #ramp up
        for i in range(0,int(1620*mod),50):
            table.turn(i)
            time.sleep(.03)
        time.sleep(.06)#Wait for blade to reach full speed
    #1
        table.turn(1620*mod) #Turn pizza at 60rpm
        table.move(-.65,12000*mod)        
        time.sleep(1/mod) #Wait for full rotation 4[pep]/4[pep/s]
    #2    
        table.turn(810*mod) #Turn the table at 30 rpm (1rpm=27Hz)
        table.move(-1.3,12000*mod) 
        time.sleep(2/mod) #Wait for full rotation 8[pep]/4[pep/s]
    #3    
        table.turn(498*mod) #Turn table at 18.462rpm
        table.move(-1.3,12000*mod) 
        time.sleep(3.25/mod)#Wait for full rotation 13[pep]/4[pep/s]
    #4    
        table.turn(405*mod) #Turn table at 15rpm
        table.move(-1.3,12000*mod)  
        time.sleep(4/mod)#Wait for full rotation 16[pep]/4[pep/s]
    #5    
        table.turn(341*mod) #Turn table at 12.632rpm
        table.move(-1.3,12000*mod) 
        time.sleep(4.75/mod)#Wait for full rotation 19[pep]/4[pep/s]
    #end    
        table.stop()
        pep.stop()
        table.move(1.3*5)#position return
class chz:
    def demo(spin=11,duration=4.2):
        dc.go(spin)#13%DC for warm dry shred, 11 for cold wet fresh
        pep.turn(1000)
        time.sleep(duration) #4.2?
        pep.stop()
        dc.go(0)
        stop()
    def spiral(speed=3,feed=300,dist=1.83):
        inps=speed/6.28 #inch per second
        spsr=inps*1600 #steps per second-radius; multiply by radius for motor speed
        dc.go(20)
        pep.turn(feed)
        table.turn(500)
        time.sleep(1)
        for radius in [dist,2*dist,3*dist]:
            table.move(-dist)
            table.turn(spsr/radius) #inps/circumference=rpm 
            time.sleep(radius/inps)#Wait for full rotation
    #end    
        table.stop()
        pep.stop()
        dc.go(0)
        
class table:
    def init(pin1=8,pin2=38):
        global turnclk
        turnclk=GPIO.PWM(pin1,500)
        turnclk.start(0)
        global tranclk
        tranclk=GPIO.PWM(pin2,1000)
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

class dc:
    def init():
        global dcclk
        dcclk=GPIO.PWM(7,500)
        dcclk.start(0)
    def go(speed=100):
        global dcclk
        dcclk.ChangeDutyCycle(speed)
   
def demo(ini=0):
    if ini>0:
        table.home()
        table.move(260)
    
    a=70
    b=10
    c=5
    x=7
    bladeclk.ChangeFrequency(a)
    turnclk.ChangeFrequency(b)
    tranclk.ChangeFrequency(c)
    GPIO.output(13,GPIO.LOW)
    bladeclk.ChangeDutyCycle(50)
    turnclk.ChangeDutyCycle(50)
    print('start')
    while a<1000:
        a=a+7
        b=a/(x)
        bladeclk.ChangeFrequency(a)
        turnclk.ChangeFrequency(b)
        time.sleep(0.01)
    print('at speed, b = ',b)
    tranclk.ChangeDutyCycle(50)
    for i in range(0,120): #duration of perimeter
        time.sleep(.1)
    print('perimeter done')
    while x>1.5:
        b=a/(x)
        c=b/6
        turnclk.ChangeFrequency(b)
        for i in range(int(c)):        
            GPIO.output(15,GPIO.HIGH)
            time.sleep(0.001)
            GPIO.output(15,GPIO.LOW)
            time.sleep(0.001)
        time.sleep(.01)
        x=x-(c*.0005)
    print('slowing')
    while a>42:
        a=a-7
        b=a/(x)
        c=b/1
        bladeclk.ChangeFrequency(a)
        turnclk.ChangeFrequency(b)
        time.sleep(0.01)
    print('done')
    bladeclk.ChangeFrequency(10)
    bladeclk.ChangeDutyCycle(0)
    turnclk.ChangeDutyCycle(0)
    time.sleep(1)
    table.move(-75)
    
    
    #while x>1:
        #step tran
        
        #adjust table turn
    
    
    
    
def stop():
    dc.go(0)
    pep.stop()
    table.stop()
    

    
#########################################INITIALIZE################################
pep.init()
table.init()
dc.init()

# Set Switch GPIO as input
# Pull high by default
GPIO.add_event_detect(11, GPIO.BOTH, callback=sensorCallback, bouncetime=200)

GPIO.setup(40, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(40, GPIO.BOTH, callback=switchCallback, bouncetime=200)