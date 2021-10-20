import RPi.GPIO as GPIO
import serial
import time
import threading
import matplotlib.pyplot as plt
import stepper
  
#***********************************VARIABLE DECLARATIONS***********************************
Weight={
    7:.10,
    10:.22,
    12:.32,
    14:.44
    }
maskSpot={
    7:7,
    10:4,
    12:2,
    14:0
}

#***************************************MOTOR SET UP****************************************
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(7,GPIO.OUT)
table=stepper.motor(15,13)
auger=stepper.motor(37,35)
mask=stepper.motor(24,26)
class conveyor:
    def go():
        GPIO.output(7,1)
    def stop():
        GPIO.output(7,0)
#******************************************FUNCTIONS******************************************
def chz(size=14,adj=1):
    ustep=8 #microstep setting on stepper driver
    dstep=[64] #initial speed (steps per load cell sample)
    maxspeed=300  #table max steps per 0.3 sec
    minspeed=20 #table min steps per 0.3 sec
    igain=1.5 #integral control parameter coefficient
    dgain=.4 #derivative control parameter coefficient
    dsdw=int(200*ustep/Weight[size]) #target weight for derivative slice
    sample_time=0.2 #calibrate to processor capacity
    
    scale.tare()
    mask.step(maskSpot[size],100)
    auger.turn(-round(600*size/14)) #this might need work
    conveyor.go()
    chzwt=[0,scale.read()]
    timeout=0
#loop to stop if no cheese comes out
    while chzwt[1]==0:
        chzwt=[0,scale.read()]
        timeout=timeout+1
        if timeout>20:
            print('no cheese')
            auger.stop()
            #conveyor stop
            return None
    step_total=0 #total steps
    ichange=[1]
    dchange=[1]
#loop to apply cheese
    while step_total<200*ustep:
        tturn=threading.Thread(target=table.step,args=(dstep[-1],dstep[-1]/sample_time,))
        tturn.start()
        chzwt.append(scale.read())
        step_total=sum(dstep)
        if chzwt[-1]>Weight[size]:
            print('weight')
            break
    #integral calculator
        inext=(200*ustep*chzwt[-1]/(step_total*Weight[size]))**igain
        if inext>1.5: inext=1.5
        elif inext<.5: inext=.5
        ichange.append(inext)
    #derivative calculator
        seg_wt=chzwt[-1]-chzwt[-2]
        if seg_wt<.01: seg_wt=.01
        dnext=((seg_wt)*dsdw/dstep[-1])**dgain
        if dnext>1.5: dnext=1.5
        elif dnext<.5: dnext=.5
        dchange.append(dnext)
    #assign next step count and prepare next loop    
        print(dstep[-1])#,'\t d:',round(dchange[-1],3),', i:',round(ichange[-1],3))
        dstep.append(int(dstep[-1]*dchange[-1]*ichange[-1]))
        if dstep[-1]<minspeed: dstep[-1]=minspeed
        if dstep[-1]>maxspeed: dstep[-1]=maxspeed
        tturn.join()
#stop all and run debug        
    stop()
    time.sleep(.5)
    chzwt.append(scale.read())
    x=round(chzwt[-1]-Weight[size],3)
    print(chzwt[-1],'-',Weight[size],'=',x)
    mask.step(-maskSpot[size],100)
    
    plt.plot(list(range(len(chzwt))),chzwt,label='wt.')
    plt.plot(list(range(len(dchange))),dchange,label='d')
    plt.plot(list(range(len(ichange))),ichange,label='i')
    plt.legend()
    plt.show()
def stop():
    auger.stop()
    mask.stop()
    table.stop()
    conveyor.stop()
def prime():
    auger.step(500,300)
    auger.step(1800,-300)
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

#***********Initialize Screen***********#
from tkinter import *
window=Tk() #Create a window

def killscreen():   #Program kills main window
    window.destroy()

def cancel():   #Changes state variable to cancel pep choice
    global state
    global top
    state=1
    stop()
    time.sleep(1.5)
    top.destroy()

window.overrideredirect(1) #Full screen if uncommented
window.geometry('480x520')
window.title("Sm^rt Chz")
#Window label:
namelabel=Label(window, text="Sm^rt Chz",)
namelabel.place(x=200,y=0)

#R4R Buttons:
text14=Button(window, text="14\"", bg="black", fg="white", command=lambda:chz(14),height=10,width=20)
text14.place(x=250, y=230)
text12=Button(window, text="12\"", bg="black", fg="white", command=lambda:chz(12),height=10,width=20)
text12.place(x=20, y=230)
text10=Button(window, text="10\"", bg="black", fg="white", command=lambda:chz(10),height=10,width=20)
text10.place(x=250, y=30)
text07=Button(window, text="7\"", bg="black", fg="white", command=lambda:chz(7),height=10,width=20)
text07.place(x=20, y=30)

#Safety and Functional Buttons:
exitbutton= Button(window, text="EXIT",bg="green", fg="white", command=killscreen,height=5, width=11)
exitbutton.place(x=330, y=430)
StopButton=Button(window,text="STOP",bg="red",fg="white",command=stop(),height=5,width=11)
StopButton.place(x=20,y=430)

window.mainloop()