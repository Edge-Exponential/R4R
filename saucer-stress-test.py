# Sm^rt Saucer Software Stress Test
import serial
import sys
import threading
import time
from tkinter import *
from tkinter import ttk
import tkinter.font as font

filepath = '/home/pi/Documents/SaucerCode/'

if hasattr(serial, 'Serial'):
    ser = serial.Serial("/dev/ttyS0", 115200)  # opens port with baud rate

turn_table_speed = 2500 #period in us, 3200 steps/rev
clean_prime_speed = 1250 #period in us, 400 steps/rev

# Variables for emergency stop
global shutdown
shutdown = False
global running
running = [0,0,0,0,0] #OFF=0, CW=1, CCW=-1
global devmode
devmode = True

# *************************************BUTTON FUNCTIONS**************************************
def stop():
    global shutdown
    shutdown = True

    ser.write("$STEPPER_STOP,PUMP1\r\n".encode())
    ser.write("$STEPPER_STOP,PUMP2\r\n".encode())
    ser.write("$STEPPER_STOP,PUMP3\r\n".encode())
    ser.write("$STEPPER_STOP,PUMP4\r\n".encode())
    ser.write("$STEPPER_STOP,TURNTABLE\r\n".encode())
    
def enable_devmode():
    global devmode
    devmode = True

# **************************************CLEAN AND PRIME**************************************
def clean(button): #GO button
    global shutdown
    shutdown = False
    c = threading.Thread(target=clean_program, args=(button,))
    c.start()

def clean_program(button): 
    global shutdown, running
    clean_time = time.time()
    old_running = [0,0,0,0,0]
    while not shutdown:
        button['text'] = int(time.time() - clean_time)
        for i in [0,1,2,3,4]:
            running[i] = zone_val[i].get()*100*rev_val[i].get()
            if running[i]!=old_running[i]:
                if i == 0: motor = 'TURNTABLE'
                else: motor = 'PUMP' + str(i)
                    
                if running[i] == 0:
                    msg = ('$STEPPER_STOP,'+motor+'\r\n')
                    ser.write(msg.encode())
                else:
                    direction = 'FORWARD'
                    if running[i] < 0:
                        direction = 'REVERSE'
                    speed = str(abs(running[i]))
                    msg = "$STEPPER_STOP,"+motor+"\r\n"
                    ser.write(msg.encode())
                    time.sleep(.1)
                    msg = "$STEPPER_START,"+motor+','+direction+','+speed+",0\r\n"
                    print(msg, end='')
                    ser.write(msg.encode())
                old_running[i] = running[i]
    time.sleep(.1)
    stop()
    button.config(text='GO')

def run_saucer(button): 
    button.config(state=DISABLED)
    global shutdown
    shutdown = False
    sauce = threading.Thread(target=sauce_program,args=(button,))
    sauce.start()

def sauce_program(button):
    global shutdown
    spd1=[0,0,0,0,0]
    cycles=1
    while not shutdown and cycles<180:        
        for i in range(5):
            button.config(text=str(cycles))
            spd1[i] = zone_val[i].get()*100
            if i == 0:
                motor = 'TURNTABLE'
                speed = '2500' #str(spd1[i])
            else:
                motor = 'PUMP' + str(i)
                speed = '800' #str(spd1[i])
            direction='FORWARD'
            startstr = "$STEPPER_START,"+motor+','+direction+','+speed+",0\r\n"
            ser.write(startstr.encode())
        
        cycletime=8 #seconds
        while not shutdown and cycletime>0:
            time.sleep(.2)
            cycletime-=.2
        if shutdown: break    
        stop()
        shutdown=False
        time.sleep(2)
        cycles+=1
    button.config(state=NORMAL,text="ENDURANCE\n30 MIN TEST")

def sequential():
    global shutdown
    shutdown = False
    sauce = threading.Thread(target=sequential_program)
    sauce.start()
    
def sequential_program(): #individual test button
    for i in range(5):
        for speed in [4000,2000,800]:
            speed=str(speed)
            if i == 0:
                motor = 'TURNTABLE'
            else:
                motor = 'PUMP' + str(i)
            direction='FORWARD'
            startstr = "$STEPPER_START,"+motor+','+direction+','+speed+",0\r\n"
            ser.write(startstr.encode())
            for t in range(30):
                if shutdown: break
                time.sleep(.1)
            stopstr = "$STEPPER_STOP,"+motor+"\r\n"
            ser.write(stopstr.encode())
            time.sleep(.5)
            if shutdown: break
        if shutdown: break
    stop()
        
def THX():
    start=[0,21,22,16,17]
    end=[0,12,16,38,48]
    for i in range(25):
        for num in [1,2,3,4]:
            period=(end[num]-start[num])*i/24+start[num]
            mcstring='$STEPPER_STOP,PUMP'+str(num)+'\r\n'
            ser.write(mcstring.encode())
            mcstring='$STEPPER_START,PUMP'+str(num)+',FORWARD,'+str(int(period)*100)+',0\r\n'
            ser.write(mcstring.encode())
        time.sleep(.2)
    time.sleep(3)
    stop()
# *****************************************HELP MENU*****************************************
# Function for changing button text based on answer

def destroy_all_screens():
    for widget in screen.winfo_children():
        if isinstance(widget, Toplevel):
            widget.destroy()

# ***********************************OTHER SCREEN SET UP*************************************
# Function setting up ... screen with various helpful features
screen = Tk()
screen.geometry('800x480')
screen.title("Sm^rt Saucer")

# Fonts for screen
small_font = font.Font(family='Helvetica', size=10, weight='normal')
med_font = font.Font(family='Helvetica', size=13, weight='bold')
diag_font = font.Font(family='Helvetica', size=19, weight='normal')
heading_font = font.Font(family='Helvetica', size=20, weight='normal')
description_font = font.Font(family='Helvetica', size=20, weight='normal')
title_font = font.Font(family='Helvetica', size=20, weight='bold')
other_font = font.Font(family='Helvetica', size=24, weight='normal')
data_size_font = font.Font(family='Helvetica', size=25, weight='normal')
calib_font = font.Font(family='Helvetica', size=30, weight='normal')
phone_font = font.Font(family='Helvetica', size=45, weight='bold')
stop_font = font.Font(family='Helvetica', size=50, weight='bold')
main_size_font = font.Font(family='Helvetica', size=52, weight='bold')


if devmode: #display speed controls
    zone_label=['TT','P1','P2','P3','P4']
    zone_val = []
    rev_val = []
    zone_scale = []
    fwdButton = []
    revButton = []
    nullButton = []
    scaleFrame = {0:Frame(),1:Frame(),2:Frame(),3:Frame(),4:Frame()}
    for zn in [0,1,2,3,4]:
        val1 = IntVar()  # all buttons are touching the same value
        val1.set(0)
        zone_val.append(val1)
        zone_scale.append(Scale(scaleFrame[zn], orient=VERTICAL,length=250, width=30, from_=0, to=48,
                                    font=med_font, variable=zone_val[zn], tickinterval=.2,label=zone_label[zn]))
        zone_scale[zn].pack(side=TOP)
        
        val2 = IntVar()
        val2.set(0)
        rev_val.append(val2)
        fwdButton.append(ttk.Radiobutton(scaleFrame[zn],text='FWD',variable=rev_val[zn],value=1))
        revButton.append(ttk.Radiobutton(scaleFrame[zn],text='REV',variable=rev_val[zn],value=-1))
        nullButton.append(ttk.Radiobutton(scaleFrame[zn],text='OFF',variable=rev_val[zn],value=0))
        revButton[zn].pack(side=BOTTOM)
        nullButton[zn].pack(side=BOTTOM)
        fwdButton[zn].pack(side=BOTTOM)
        scaleFrame[zn].pack(side=LEFT)

buttonFrame = Frame()
if devmode:
    goButton = Button(buttonFrame, text="START", font=med_font,bg='green', fg='white',
                      command=lambda: clean(goButton), height=2, width=40)
    goButton.pack(side=TOP)
stopButton=Button(buttonFrame,text="STOP",font=med_font,bg="red",fg="white",
                  command=stop, height=2, width=40)
stopButton.pack(side=TOP)
Label(buttonFrame,text='',font=med_font,height=1, width=40).pack(side=TOP)
seqButton=Button(buttonFrame,text="INDIVIDUAL\nMOTOR TEST",font=med_font,command=sequential,height=2,width=40)
seqButton.pack(side=TOP)
simButton=Button(buttonFrame,text="ENDURANCE\n30 MIN TEST",font=med_font,command=lambda:run_saucer(simButton),height=2,width=40)
simButton.pack(side=TOP)
if devmode:
    thxButton=Button(buttonFrame,text="THX",font=med_font,command=THX,height=2,width=40)
    thxButton.pack(side=TOP)
    buttonFrame.pack(side=RIGHT,padx=50)
else: buttonFrame.pack(pady=20)

mainloop()
