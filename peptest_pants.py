import RPi.GPIO as GPIO
import time
import datetime
import sys
import signal
from tkinter import ttk
import numpy as np
import _thread
#***********************************VARIABLE DECLARATIONS***********************************

#***************************************MOTOR SET UP****************************************

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

GPIO.setup(18 , GPIO.IN, pull_up_down=GPIO.PUD_UP) #limit switch
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

#***********Initialize Screen***********#
from tkinter import *
window=Tk()
def killscreen():
    window.destroy()

def cancel():
    global state
    global top
    state=1
    stop()
    top.destroy()
    
stopFont=font.Font(family='Helvetica', size=50, weight='bold')
font=font.Font(family='Helvetica', size=20, weight='normal')

window.overrideredirect(1)
window.geometry('800x480')
window.title("Sm^rt Pep")
namelabel=Label(window, text="Sm^rt Pep", font=font)
namelabel.place(x=250,y=0)
RR=Label(window, text="R4R:", font=font)
RR.place(x=0,y=35)

def open_popup():
    global top
    top=Toplevel(window)
    top.overrideredirect(1)
    top.geometry("800x480")
    top.title("Stop Window")
    Label(top, text="Press Button to Cancel",font=font).place(x=185,y=0)
    Button(top,text="CANCEL",bg="red",fg="white",command=cancel,height=15,width=25).place(x=205,y=100)
    Button(top,text="EXIT",command=top.destroy).place(x=290,y=375)
#*******************************Arrays************#
Large=2*np.array([20,17,13,6,4])
FLarge=2*np.array([33,27,20,18,6,1])
Finish_Large=2*np.array([13,10,7,12,2])
Medium=[16,11,6,1]
Small=[15,10,5]
Indiv=[8,4,1]


global n_pep
global blade_speed
n_pep=0

global Tstart
global Tstop
Tstart=time.time()
Tstop=time.time()
blade_speed=150
global state
state=0
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
    #print(deltaT)
    blade_speed=30/deltaT
    
            
#Interrupt that triggers on the falling edge of when a magnet is sensed and calls the prog rotations
GPIO.add_event_detect(12,GPIO.FALLING,callback=rotations,bouncetime=100)

#******************************************FUNCTIONS******************************************
        
class blade:
    def init():
        global bladeclk
        bladeclk=GPIO.PWM(36,500) #Define Pin 7, 500Hz
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
    def Move(dist):
        _thread.start_new_thread(table.move,(dist,))
            
    def trans(dist,freq):
        if dist>0:
            GPIO.output(29,0)
        else:
            GPIO.output(29,1)
        global tranclk
        if freq==0:
            tranclk.ChangeDutyCycle(0)
        else:
            tranclk.ChangeDutyCycle(50)
            tranclk.ChangeFrequency(freq)
            
    def turn(freq):
        global turnclk
        GPIO.output(15,1)
        if freq==0:
            turnclk.ChangeDutyCycle(0)
        else:
            turnclk.ChangeDutyCycle(50)
            turnclk.ChangeFrequency(freq)
        
    def stop():
        global turnclk
        global tranclk
        turnclk.ChangeDutyCycle(0)
        tranclk.ChangeDutyCycle(0)
    
def stop():
    global state
    state=1
    table.stop()
    blade.stop()

  
def calc(num_pep):
    global T_freq
    global blade_speed
    steps=200
    micro=16
    total_steps=steps*micro
    step_angle=360/total_steps
    pps=blade_speed/30 #Pep per sec
    
    T_rpm=60/(num_pep/pps)
    T_freq=T_rpm/((step_angle/360)*60) #Frequency to run table
    table.turn(T_freq)
    
def advance(pep_need):
    global T_freq
    global state
    global n_pep
    while n_pep<pep_need and state==0:
        window.update()
        calc(pep_need)
    n_pep=0
    
def home():
    while GPIO.input(18)==1:
        GPIO.output(29,1)
        table.trans(-1,50000)
    table.stop()
    
#########################################INITIALIZE################################
blade.init()
table.init()
 #########################################Home Interrupt########################################

#switch sensor callback
def detect(channel):
    if GPIO.input(18)==0: #Table home
        table.stop() #Stop the rotation and translation of the table

GPIO.add_event_detect(18,GPIO.FALLING, callback=detect,bouncetime=100)
########################################DEMO########################################
      
global speed   
speed=36   

def R_Large():
        global state
        open_popup()
        state=0
        table.move(5.25)
        time.sleep(.2)
        global Tstart
        global Tstop
        Tstart=time.time()
        Tstop=time.time()
        blade.turn(speed)
        advance(Large[4]) #Wait 1.6s for full rotation 4[pep]/4[pep/s]
        
        table.Move(-1.5)
        advance(Large[3])    
    
        table.Move(-1.3)
        advance(Large[2])
        
        table.Move(-1.3)
        advance(Large[1])

        table.Move(-1.3)
        advance(Large[0])
        blade.stop()
        table.stop()
    
        table.Move(-.3)
        top.destroy()
        stop()
        
def R_Medium():
        global state
        state=0
        open_popup()
        table.move(4.7)
        time.sleep(.2)
        blade.turn(speed)
        advance(Medium[3])
        
        table.move(-1.3)
        advance(Medium[2])
        
        table.move(-1.3)
        advance(Medium[1])
        
        table.move(-1.3)
        advance(Medium[0])
        stop()
        
def R_Small():
        global state
        state=0
        open_popup()
        table.move(2.7)
        time.sleep(.2)
        blade.turn(speed)
        advance(Small[2])
        
        table.move(-1.3)
        advance(Small[1])
        
        table.move(-1.3)
        advance(Small[0])
        
def R_indiv():
    global state
    state=0
    open_popup()
    table.move(1.2)
    time.sleep(.2)
    blade.turn(speed)
    advance(Indiv[2])
       
    table.move(-.75)
    advance(Indiv[1])
        
    table.move(-.25)
    advance(Indiv[0])


def F_Large():
        global state
        open_popup()
        state=0
        table.move(6)
        time.sleep(.2)
        global Tstart
        global Tstop
        Tstart=time.time()
        Tstop=time.time()
        blade.turn(speed)
        advance(FLarge[5]) #Wait 1.6s for full rotation 4[pep]/4[pep/s]
        
        table.move(-1.2)
        advance(FLarge[4])    
    
        table.move(-1.3)
        advance(FLarge[3])
        
        table.move(-1.3)
        advance(FLarge[2])

        table.move(-1.3)
        advance(FLarge[1])
    
        table.move(-1.3)
        advance(FLarge[0])
        blade.stop()
        table.stop()
        
        table.move(-.3)
        top.destroy()
        stop()
        
def Finish_Large():
        global state
        #open_popup()
        state=0
        table.move(5.25)
        time.sleep(.2)
        global Tstart
        global Tstop
        Tstart=time.time()
        Tstop=time.time()
        blade.turn(speed)
        advance(Finish_Large[4]) #Wait 1.6s for full rotation 4[pep]/4[pep/s]
        
        table.Move(-1.5)
        advance(Finish_Large[3])    
    
        table.Move(-1.3)
        advance(Finish_Large[2])
        
        table.Move(-1.3)
        advance(Finish_Large[1])

        table.Move(-1.3)
        advance(Finish_Large[0])
        blade.stop()
        table.stop()
    
        table.Move(-.3)
        #top.destroy()
        stop()
    

def Spiral():
    global state
    state=0
    table.move(5.5)
    time.sleep(.2)
    global Tstart
    global Tstop
    Tstart=time.time()
    Tstop=time.time()
    blade.turn(speed)
    table.trans(-1,1000)
    table.turn(1250)
    time.sleep(.2)
    advance(Large[4]) #Wait 1.6s for full rotation 4[pep]/4[pep/s]
    table.trans(-1,1000)
    table.turn(1100)
    advance(Large[3])
    table.turn(750)
    table.trans(-1,800)
    advance(Large[2])
    table.turn(625)
    table.trans(-1,650)
    advance(Large[1])
    table.turn(450)
    table.trans(450 )
    advance(Large[0])
    state=1
    blade.stop()
    table.stop()
    stop()

#******Screen Code*******
text14=Button(window, text="14\"", font=font, bg="black", fg="white", command=R_Large,height=3, width=8)
text14.place(x=470, y=70)
text12=Button(window, text="12\"", font=font, bg="black", fg="white", command=R_Medium,height=3,width=8)
text12.place(x=320, y=70)
text10=Button(window, text="10\"", font=font, bg="black", fg="white", command=R_Small,height=3, width=8)
text10.place(x=170, y=70)
text07=Button(window, text="7\"", font=font, bg="black", fg="white", command=R_indiv,height=3,width=8)
text07.place(x=20, y=70)

FullPep=Label(window, text="Full Pep:", font=font)
FullPep.place(x=0,y=180)


F_Large=Button(window, text="14\"", font=font, bg="black", fg="white", command=F_Large,  height=3, width=8)
F_Large.place(x=470,y=215)
F_Medium=Button(window,text="12\"",font=font,bg="black",fg="white",command=killscreen,height=3,width=8)
F_Medium.place(x=320,y=215)
F_Small=Button(window,text="10\"",font=font,bg="black",fg="white",command=killscreen,height=3,width=8)
F_Small.place(x=170,y=215)
F_indiv=Button(window,text="7\"",font=font,bg="black",fg="white",command=killscreen,height=3,width=8)
F_indiv.place(x=20,y=215)


exitbutton= Button(window, text="EXIT", font=font,bg="green", fg="white", command=killscreen,height=2, width=9)
exitbutton.place(x=475, y=400)
homeButton=Button(window,text="Table Home",font=font,bg="green",fg="white",command=home,height=2,width=9)
homeButton.place(x=5,y=400)

StopButton=Button(window,text="STOP", font=font,bg="red",fg="white",command=stop(),height=3,width=11)
StopButton.place(x=220,y=367)
Button(window,text="Cancel Popup",command=open_popup).place(x=5,y=350)

window.mainloop()