import RPi.GPIO as GPIO
import time
import datetime
  
#***********************************VARIABLE DECLARATIONS***********************************


#***************************************MOTOR SET UP****************************************

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

GPIO.setup(11 , GPIO.IN, pull_up_down=GPIO.PUD_UP) #limit switch

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
        for i in range(oldfreq,newfreq,10*(2*(newfreq>oldfreq)-1)):
            bladeclk.ChangeFrequency(i)
            time.sleep(.03)
        oldfreq=newfreq    
            
    def stop():
        pep.turn(100)
        bladeclk.ChangeDutyCycle(0)
        
    def end():
        bladeclk.stop()

    def sw():
        pep.stop()
        if GPIO.input(16)==0:
            GPIO.output(16,GPIO.HIGH)
        else:
            GPIO.output(16,GPIO.LOW)
class table:
    def init(pin1=8,pin2=15):
        global turnclk
        turnclk=GPIO.PWM(pin1,500)
        turnclk.start(0)
        global tranclk
        tranclk=GPIO.PWM(pin2,1000)
        tranclk.start(0)
        
    def move(dist,freq=2000,pin3=13):
        global REV

        REV = 0 #Revolution Count
        VAl = 0 #Currrent mag value
        TEMP = 0 #Previous mag value
        PRESS = 0 #switch value
        
        trandir=dist<0
        GPIO.output(pin3,trandir)
        global tranclk
        tranclk.ChangeFrequency(freq)
        tranclk.ChangeDutyCycle(50)
        for i in range(abs(dist)):
            time.sleep(0.1)
            PRESS = switchCallback(40)
            if PRESS == 1:
                break
            VAL = sensorCallback(11)

            
            
            if TEMP == 0 and VAL == 1:
                REV = REV + 0.5
                TEMP = 1
                print('Rvolution count: ')
                print(REV)
            else:
                TEMP = 0

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

class shake:
    def init():
        global shakeclk
        shakeclk=GPIO.PWM(7,500)
        shakeclk.start(0)
    def turn(speed=100):
        global shakeclk
        shakeclk.ChangeDutyCycle(speed)

def cut(bladefreq=1400,tablefreq=200):
    table.turn(tablefreq)
    pep.turn(bladefreq)
    
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
    pep.stop()
    table.stop()

    
#########################################INITIALIZE################################
pep.init()
table.init()
# Set Switch GPIO as input
# Pull high by default
GPIO.add_event_detect(11, GPIO.BOTH, callback=sensorCallback, bouncetime=200)

GPIO.setup(40, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(40, GPIO.BOTH, callback=switchCallback, bouncetime=200)
