import RPi.GPIO as GPIO
import time
import datetime
import sys
import signal
from tkinter import ttk
import numpy as np
import _thread
#***************************************SETUP****************************************

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
window=Tk() #Create a window

def killscreen():   #Program kills main window
    window.destroy()

def cancel():   #Changes state variable to cancel pep choice
    global state
    global top
    state=1
    stop()
    top.destroy()
    
stopFont=font.Font(family='Helvetica', size=50, weight='bold')
font=font.Font(family='Helvetica', size=20, weight='normal')    #Main font

window.overrideredirect(1) #Full screen if uncommented
window.geometry('800x480')
window.title("Sm^rt Pep")
#Window label:
namelabel=Label(window, text="Sm^rt Pep", font=font)
namelabel.place(x=250,y=0)
#Screen section labels:
RR=Label(window, text="R4R:", font=font)
RR.place(x=0,y=35)
FullPep=Label(window, text="Full Pep:", font=font)
FullPep.place(x=0,y=180)


def open_popup(): #Opens a popup window that the user can use to cancel pep choice
    global top
    top=Toplevel(window)
    top.overrideredirect(1)
    top.geometry("800x480")
    top.title("Stop Window")
    Label(top, text="Press Button to Cancel",font=font).place(x=185,y=0)
    Button(top,text="CANCEL",bg="red",fg="white",command=cancel,height=15,width=25).place(x=205,y=100) #Button to cancel pep choice
    Button(top,text="EXIT",command=top.destroy).place(x=290,y=375) #Button to exit the popup

#***********************Arrays******************************#
#Arrays multiplied by two to account for both magnets (2mag=1pep)
Large=2*np.array([20,17,13,6,4])+1 #R4R Large
FLarge=2*np.array([33,27,20,18,6,1])+1 #Full Large
Finish_Large=2*np.array([13,10,7,12,2])+1 #40 on 60 Large

Medium=2*np.array([16,11,6,1]) #R4R Medium
FMedium=2*np.array([28,21,15,8,1]) #Full Medium
Finish_Medium=2*np.array([12,10,9,7])

Small=2*np.array([15,10,5])
FSmall=2*np.array([22,16,9,3])
Finish_Small=2*np.array([7,6,4])
                  
Indiv=2*np.array([8,4,1])
FIndiv=2*np.array([12,7,1])
Finish_Indiv=2*np.array([4,3])

#***********************Variable Declaration******************************#
global n_pep    #Pep cut variable
global blade_speed  #Blade speed var for instantaneous blade speed
global Tstart
global Tstop
global state
    
global revolutions

#***********************Variable Initialization******************************#
n_pep=0 #Initialize pep cut
blade_speed=150 #Initialize blade speed
state=0 #Initialize the state variable for cancelling
    
#***********************Rotary Interrupt******************************#
#Detects magnet indicating half rotation; Calculates blade speed
def rotations(self):
    global n_pep
    global blade_speed
    global Tstart
    global Tstop
    n_pep=n_pep+1 #Advance number of detections by 1
    print(n_pep)
    Tstart=Tstop
    Tstop=time.time()
    deltaT=Tstop-Tstart
    #print(deltaT)
    blade_speed=30/deltaT
    
    if blade_speed>=160:
                  stop()
            
#Interrupt that triggers on the falling edge of when a magnet is sensed and calls the prog rotations
GPIO.add_event_detect(12,GPIO.FALLING,callback=rotations,bouncetime=100)

#***********************Primary Functions******************************#
        
class blade:
    def init():
        global bladeclk
        bladeclk=GPIO.PWM(36,500) #Define Pin 36, 500Hz
        bladeclk.start(0) #Stop the blade
                  
    def turn(speed=0):
        global bladeclk
        bladeclk.ChangeDutyCycle(speed) #Change the duty cycle of blade motor to user input
        
    def begin(SPEED):
        global speed
        global blade_speed
        blade.turn(SPEED)
        while blade_speed<20:
                  SPEED=SPEED+1
                  blade.turn(SPEED)
        blade.turn(speed)
                  
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
        #Set motor to proper direction
        if dist>0:
            GPIO.output(29,0)
        else:
            GPIO.output(29,1)
            
        global REV
        REV=abs(dist)*200*16/(3.1415926536*.40098425196) #Convert distance to steps on motor (dist*steps*microStep/(pi*pitchDiam))
        REV=round(REV)
        #Step motor manually for given distance
        for i in range(0,REV):
            GPIO.output(pin3,1)
            time.sleep(1/(2*freq))
            GPIO.output(pin3,0)
            time.sleep(1/(2*freq))
    
    def Move(dist): #Thread the table.move function
        _thread.start_new_thread(table.move,(dist,))
    
    #Function moves table at a given frequency and direction (-1 or 1 for direction)
    def trans(dir,freq):
        if dir>0:
            GPIO.output(29,0)
        else:
            GPIO.output(29,1)
    
        global tranclk
        if freq==0:
            tranclk.ChangeDutyCycle(0)
        else:
            tranclk.ChangeDutyCycle(50)
            tranclk.ChangeFrequency(freq)
            
    #Turn table at given frequency
    def turn(freq):
        global turnclk
        GPIO.output(15,1) #CCW direction HIGH, CW direction LOW
        if freq==0:
            turnclk.ChangeDutyCycle(0)
        else:
            turnclk.ChangeDutyCycle(50)
            turnclk.ChangeFrequency(freq)
    
     #Stop all table movement
    def stop():
        global turnclk
        global tranclk
        turnclk.ChangeDutyCycle(0)
        tranclk.ChangeDutyCycle(0)
    
#Stop all machine movement
def stop():
    global state
    state=1 #Change state of while loops to terminate
    table.stop()
    blade.stop()

#Claculates and sets the freqency of table for given num of pep
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

#Wait loop that calls calc to continuously update table rotation for given pep num and row    
def advance(pep_need):
    global T_freq
    global state
    global n_pep
    while n_pep<pep_need and state==0:
        window.update()
        calc(pep_need)
    n_pep=0 #Reset pep cut to start next row

#Homes the table
def home():
    while GPIO.input(18)==1:
        GPIO.output(29,1)
        table.trans(-1,50000)
    table.stop()
    
#***********************Initialize******************************#
blade.init()
table.init()
    
#***********************Home Stop Interrupt******************************#
#switch sensor callback
def detect(channel):
    if GPIO.input(18)==0: #Table is home
        table.stop() #Stop the rotation and translation of the table

GPIO.add_event_detect(18,GPIO.FALLING, callback=detect,bouncetime=100)
    
#***********************Pizza Programs******************************#
global speed   
speed=36   

#Full Pep:    
def R_Large():
        global state
        state=0 #Ensure the program will run advance()
        open_popup() #Open cance window
        home()
        table.move(5.25) #Move table to first row
        time.sleep(.2)
        global Tstart
        global Tstop
        Tstart=time.time()
        Tstop=time.time()
        blade.begin(speed)
        advance(Large[4])
        
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
    
        home()
        top.destroy()
        stop()
        
def R_Medium():
        global state
        state=0 #Ensure the program will run advance()
        open_popup()
        home()
        table.move(4.7) #Move table to first row
        time.sleep(.2)
        blade.begin(speed)
        advance(Medium[3])
        
        table.move(-1.3)
        advance(Medium[2])
        
        table.move(-1.3)
        advance(Medium[1])
        
        table.move(-1.3)
        advance(Medium[0])
        home()
        top.destroy()
        stop()
        
def R_Small():
        global state
        state=0
        open_popup()
        table.move(2.7) #Move table to first row
        time.sleep(.2)
        blade.begin(speed)
        advance(Small[2])
        
        table.move(-1.3)
        advance(Small[1])
        
        table.move(-1.3)
        advance(Small[0])
       
        home()
        top.destroy()
        stop()
        
def R_indiv():
    global state
    state=0
    open_popup()
    table.move(1.2) #Move table to first row
    time.sleep(.2)
    blade.begin(speed)
    advance(Indiv[2])
       
    table.move(-.75)
    advance(Indiv[1])
        
    table.move(-.25)
    advance(Indiv[0])
    
    home()
    top.destroy()
    stop()

#Full Pep:
def F_Large():
        global state
        open_popup()    
        state=0
        table.move(6) #Move table to first row
        time.sleep(.2)
        global Tstart
        global Tstop
        Tstart=time.time()
        Tstop=time.time()
        blade.begin(speed)
        advance(FLarge[5])
        
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
        
        home()
        top.destroy()
        stop()
                  
def F_Medium():
        global state
        open_popup()    
        state=0
        table.move(6) #Move table to first row
        time.sleep(.2)
        global Tstart
        global Tstop
        Tstart=time.time()
        Tstop=time.time()
        blade.begin(speed)
        advance(FMedium[4])
        
        table.move(-1.2)
        advance(FMedium[3])    
    
        table.move(-1.3)
        advance(FMedium[2])
        
        table.move(-1.3)
        advance(FMedium[1])

        table.move(-1.3)
        advance(FMedium[0])
        
        home()
        top.destroy()
        stop()
                  
def F_Small():
        global state
        open_popup()    
        state=0
        table.move(6) #Move table to first row
        time.sleep(.2)
        global Tstart
        global Tstop
        Tstart=time.time()
        Tstop=time.time()
        blade.begin(speed)
        advance(FSmall[3])
        
        table.move(-1.2)
        advance(FSmall[2])    
    
        table.move(-1.3)
        advance(FSmall[1])
        
        table.move(-1.3)
        advance(FSmall[0])
        
        home()
        top.destroy()
        stop()                  

def F_Indiv():
        global state
        open_popup()    
        state=0
        table.move(6) #Move table to first row
        time.sleep(.2)
        global Tstart
        global Tstop
        Tstart=time.time()
        Tstop=time.time()
        blade.begin(speed)
        advance(FIndiv[2])
        
        table.move(-1.2)
        advance(FIndiv[1])    
    
        table.move(-1.3)
        advance(FIndiv[0])
        
        home()
        top.destroy()
        stop()                  

def Large_Index():
        global speed
        global state
        open_popup()    
        state=0
        table.move(6) #Move table to first row
        time.sleep(.2)
        global Tstart
        global Tstop
        Tstart=time.time()
        Tstop=time.time()
        blade.begin(speed)
        advance(FLarge[5])
        
        blade.turn(speed/2)
        table.move(-1.2)
        blade.turn(speed)
        advance(FLarge[4])    
    
        blade.turn(speed/2)
        table.move(-1.3)
        blade.turn(speed)          
        advance(FLarge[3])
        
        blade.turn(speed/2)          
        table.move(-1.3)
        blade.turn(speed)          
        advance(FLarge[2])
        
        blade.turn(speed/2)          
        table.move(-1.3)
        table.turn(speed)         
        advance(FLarge[1])
        
        table.turn(speed/2)         
        table.move(-1.3)
        table.turn(speed)          
        advance(FLarge[0])
        blade.stop()
        table.stop()
        
        home()
        top.destroy()
        stop()
                  
#40 on 60; 14"
def Finish_Large():
        global state
        #open_popup()
        state=0
        table.move(5.25) #Move table to the first row
        time.sleep(.2)
        global Tstart
        global Tstop
        Tstart=time.time()
        Tstop=time.time()
        blade.begin(speed)
        advance(Finish_Large[4])
        
        table.Move(-1.5)
        advance(Finish_Large[3])    
    
        table.Move(-1.3)
        advance(Finish_Large[2])
        
        table.Move(-1.3)
        advance(Finish_Large[1])

        table.Move(-1.3)
        advance(Finish_Large[0])
        
        home()
        top.destroy()
        stop()
                        
#14" Spiral
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
    advance(Large[4])
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

#***********************Button Screen Code******************************#
#R4R Buttons:
text14=Button(window, text="14\"", font=font, bg="black", fg="white", command=R_Large,height=3, width=8)
text14.place(x=470, y=70)
text12=Button(window, text="12\"", font=font, bg="black", fg="white", command=R_Medium,height=3,width=8)
text12.place(x=320, y=70)
text10=Button(window, text="10\"", font=font, bg="black", fg="white", command=R_Small,height=3, width=8)
text10.place(x=170, y=70)
text07=Button(window, text="7\"", font=font, bg="black", fg="white", command=R_indiv,height=3,width=8)
text07.place(x=20, y=70)

#Full Pep Button:
F_Large=Button(window, text="14\"", font=font, bg="black", fg="white", command=F_Large,  height=3, width=8)
F_Large.place(x=470,y=215)
F_Medium=Button(window,text="12\"",font=font,bg="black",fg="white",command=F_Medium,height=3,width=8)
F_Medium.place(x=320,y=215)
F_Small=Button(window,text="10\"",font=font,bg="black",fg="white",command=F_Small,height=3,width=8)
F_Small.place(x=170,y=215)
F_indiv=Button(window,text="7\"",font=font,bg="black",fg="white",command=F_Indiv,height=3,width=8)
F_indiv.place(x=20,y=215)

#Safety and Functional Buttons:
exitbutton= Button(window, text="EXIT", font=font,bg="green", fg="white", command=killscreen,height=2, width=9)
exitbutton.place(x=475, y=400)
homeButton=Button(window,text="Table Home",font=font,bg="green",fg="white",command=home,height=2,width=9)
homeButton.place(x=5,y=400)
StopButton=Button(window,text="STOP", font=font,bg="red",fg="white",command=stop(),height=3,width=11)
StopButton.place(x=220,y=367)
    
Button(window,text="Cancel Popup",command=open_popup).place(x=5,y=350)

window.mainloop()
