import RPi.GPIO as GPIO
import serial
import time
import threading
import matplotlib.pyplot as plt
  
#***********************************VARIABLE DECLARATIONS***********************************
Weight={
    7:.10,
    10:.22,
    12:.32,
    14:.44
    }
dW=-.1 #weight diff: actual v. target

#***************************************MOTOR SET UP****************************************
pin_tturnclk=15
pin_stepclk=37
pin_stepdir=35
pin_dcr=11
pin_dcl=7
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

GPIO.setup(pin_tturnclk, GPIO.OUT) #tableturn clk
GPIO.setup(pin_stepdir, GPIO.OUT) #DM860T dir
GPIO.setup(pin_stepclk, GPIO.OUT) #DM860T clk

#******************************************FUNCTIONS******************************************
def quickrun(x0):
    for i in range(x0):
        GPIO.output(pin_tturnclk,1)
        time.sleep(0.3/x0)
        GPIO.output(pin_tturnclk,0)
        time.sleep(0.3/x0)
    
def chz(size=14,adj=1):
    ustep=8 #microstep setting on stepper driver
    dstep=[64] #initial speed (steps per quickrun)
    i_wt=2
    d_wt=.3
        
    dsdw=int(200*ustep/Weight[size]) #target weight for derivative slice
    scale.tare()
    step.turn(round(600*size/14))
    #turn on vibrating conveyor 100%
    chzwt=[scale.read()]
    timeout=0
    while chzwt[0]==0 and timeout<5:
        chzwt=[scale.read()]
        timeout=0
    step_total=0 #total steps
    ichange=[1]
    dchange=[1]
    while step_total<200*ustep: #200 step/rev * 8 microstep
        tturn=threading.Thread(target=quickrun,args=(dstep[-1],))
        tturn.start()
        chzwt.append(scale.read())
        step_total=sum(dstep)
        ichange.append((200*ustep*chzwt[-1]/(step_total*Weight[size]))**i_wt)
        dchange.append(((chzwt[-1]-chzwt[-2])*dsdw/dstep[-1])**d_wt)
        print(dstep[-1],'\t d:',round(dchange[-1],3),', i:',round(ichange[-1],3))
        dstep.append(int(dstep[-1]*dchange[-1]*ichange[-1]))
        if dstep[-1]<20: dstep[-1]=20
        if dstep[-1]>1000: dstep[-1]=1000
        tturn.join()
    step.stop()
    #conveyor stop
    table.stop()
    time.sleep(.5)
    chzwt.append(scale.read())
    plt.plot(list(range(len(chzwt))),chzwt,label='wt.')
    plt.plot(list(range(len(dchange))),dchange,label='d')
    plt.plot(list(range(len(ichange))),ichange,label='i')
    x=round(chzwt[-1]-Weight[size],3)
    print(chzwt[-1],'-',Weight[size],'=',x)
    plt.show()
    return x

# def chz(size=14,adj=0):
#     table.turn(600)
#     scale.tare()
#     chzwt=[scale.read()]
#     #turn on vibrating conveyor 100%
#     step.turn(200)
#     while chzwt[-1]<TargetWeight[size]+adj:
#         #time.sleep(.2)
#         chzwt.append(scale.read())    
#     step.stop()
#     #conveyor stop
#     table.stop()
#     time.sleep(.5)
#     chzwt.append(scale.read())
#     print(chzwt[-8:-1])
#     x=round(chzwt[-1]-TargetWeight[size],3)
#     print(chzwt[-1],'-',TargetWeight[size],'=',x)
#     return x
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

class scale:
    def init():
        global ser
        ser = serial.Serial()
        ser.port = "/dev/ttyUSB0"
        ser.baudrate = 9600
        ser.timeout = .1
        try: ser.open()
        except FileNotFoundError: print('USB not found')
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

scale.init()
table.init()
step.init()