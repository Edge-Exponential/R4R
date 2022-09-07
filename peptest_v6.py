import RPi.GPIO as GPIO
import time
import stepper
import threading
import math
import serial
import PIL.Image,PIL.ImageDraw,PIL.ImageTk


GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
lim_pin=18 #gantry limit switch
hall_pin=12 #blade shaft encoder (1 blip per rev)
ena_pin=16 #stepper motor enable, 1=disable to keep temps down
GPIO.setup(lim_pin,GPIO.IN, pull_up_down=GPIO.PUD_UP) 
GPIO.setup(hall_pin,GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ena_pin,GPIO.OUT)

tturn=stepper.motor(11,15)
ttran=stepper.motor(21,23)
tlift=stepper.motor(38,40)

pep_ratio = 3200*14/19  #steps/bladerev
pep_max = 10000
ttran_ratio = -1600    #steps/transrev
tturn_ratio = 1600    #steps/tablerev
tturn_max = .8*tturn_ratio
tlift_ratio = 400/.19196  #steps/in (0.19196in screw lead)
tlift_max = 1.5 #inch extension
n = 0
shutdown = 0

try:
    ser = serial.Serial("/dev/ttyACM0",9600)
    class pep:
        freq = 0
        def stop():
            ser.write(b'0\r\n')
            pep.freq=0
        def turn(freq):
            if freq == 0:
                pep.stop()
                return
            freq = int(1000000/(2*freq))
            ser.write(b'%d\r\n' % freq)
            pep.freq=freq
    print('ser to Arduino')
except:
    pep=stepper.motor(33,29)
    print('stepper.motor')

#***********************MechanicalFunctions******************************#   
def in2step(inch,pulleydiam=1.337/20*15):
    return int(inch*ttran_ratio/(3.14159*pulleydiam)) #Convert distance to steps on motor
def home():
    GPIO.output(ena_pin,GPIO.LOW)
    ttran.turn(3*ttran_ratio)
    while GPIO.input(lim_pin): time.sleep(.03)
    ttran.stop()
def hallblip(x):
    global n
    n+=1
    if False:
        global derf
        if 'derf' in globals():
            print(1/(time.time()-derf))
        derf=time.time()
def centercal(center=-8.2):
    ttran.step(in2step(center),12000)
    time.sleep(2)
    home()

def enable():
    GPIO.output(ena_pin,GPIO.LOW)
    
def stop():
    global shutdown
    shutdown=1
    GPIO.output(ena_pin,GPIO.HIGH)
    pep.stop()
    tturn.stop()
    ttran.stop()
    GPIO.remove_event_detect(hall_pin)
#     try:
#         for window in root.winfo_children():
#             window.destroy()
#         homescreen()
#     except Exception as e: print(' and returned to home screen but',e)
def run_pep(size=7, qty=15, pps=3 , margin=0, center=-8.1, rpep=17):
    #create pizza mockup image then run motors pep_program in thread
    
    #calculate pep pitch circle radius in mm
    r=(size/2-margin)*25.4-rpep
    
    #image dimensions/setup
    xdim=360
    ydim=180
    im=PIL.Image.new('RGB',(xdim*2,ydim*2),(200,200,200))
    draw=PIL.ImageDraw.Draw(im)
    draw.ellipse((xdim-size*12.7,ydim-size*12.7,xdim+size*12.7,ydim+size*12.7),fill=(255,219,112),outline='brown')
    
    #calculate spacing between each row in mm (delta_radius)
    dr=math.sqrt(math.pi*r*r/(.0003172*qty*qty+.8365*qty-3.9))
    
    #calculate the number of peps in each row, with some fudging to get it to look right
    npep=[]
    for m in range(math.ceil(r/dr)):
        npep.append(round((r-m*dr)*2*math.pi/dr))
    try: npep.remove(0)
    except ValueError: pass
    if npep[-1]>4:npep.append(1)
    
    #calculate row_ct and pep_ct for pep_program coordination
    row_ct=[] #how far to move to each row in inches
    pep_ct=[] #number of blade revolutions per table revolution
    nr=math.ceil(r/dr) #Number of Rows
    for m in range(nr): #for each row calculate...
        pep_ct.insert(0, round((r-m*dr) * 2*math.pi / dr)) #number of peps in row
        row_ct.insert(0, round(center + r/25.4 - m*dr/25.4, 2)) #distance from home position
    if pep_ct[0]==0:pep_ct[0]=1 #force center row to round up to 1
    if pep_ct[0]>4: #add center pep if there is space
        nr+=1
        pep_ct.insert(0,1)
        row_ct.insert(0,center)
    for m in range(nr-1,0,-1): #convert row locations from absolute to relative
        row_ct[m]=round(row_ct[m]-row_ct[m-1],2)
    
    
    #for each row; for each pep: draw a red circle
    for row in npep:
        dTheta=2*math.pi/row
        for pep in range(row):
            x=math.cos(pep*dTheta)*r+xdim
            y=math.sin(pep*dTheta)*r+ydim
            draw.ellipse((x-rpep,y-rpep,x+rpep,y+rpep),fill='red',outline='black')
        r-=dr
 
    #TkInter display finalized pep layout image:
    global algimg
    algimg=Toplevel(root)
    algimg.overrideredirect(1)
    algimg.geometry('800x480')
    Label(algimg, text='TestLabel:', font=font).place(x=75,y=0)
    Button(algimg, text="X", font=font,bg="red", fg="white", command=killscreen,height=1, width=1).place(x=0, y=0)
    Button(algimg,text="HOME",font=font,command=home,height=2,width=10).place(x=100,y=400)
    Button(algimg,text="STOP",font=font,bg="red",fg="white",command=stop,height=2,width=10).place(x=300,y=400)
    global algim
    algim=PIL.ImageTk.PhotoImage(im)
    Label(algimg,image=algim).place(x=30,y=40)
    
    size_i = 4 - math.ceil((size/2)-4) # index {14:0, 12:1, 10:2, 7:3}
    lift_steps = size_i * .25 * tlift_ratio
    
    #run pep_program with e-stop capability
    print('run_pep:',pep_ct,row_ct,'r=',round(r,2),'dr=',round(dr,2),'pps=',pps, 'tlift=',lift_steps)
    process=threading.Thread(target=pep_program ,args=(row_ct,pep_ct,pps,lift_steps))
    process.start()
    
def pep_program(row_ct,pep_ct,pps,lift_steps): #pps changes speed of the whole script
    global shutdown
    shutdown=0
    global n #blade encoder interrupt counter global var
    pizzaTime=time.time() #start timer
    
    #move gantry and start table
    GPIO.output(ena_pin,GPIO.LOW)
    home()
    
    tturn_steps = int(tturn_ratio * .2*pep_ct[0]) #rotate table 1 pep width less than 1 rev
    tturn_speed = pps*tturn_steps/pep_ct[0]
    pep_speed = pps*pep_ratio #calculate how fast to rotate blade
    if pep_speed > pep_max:
        pep_speed = pep_max
        pps = pps * abs(pep_max/pep_speed)
    tturn_speed = pps*tturn_steps/pep_ct[0]  #fit x peps in that section, assuming bladespeed of pps
    mod = 1
    if abs(tturn_speed) > tturn_max: #slow down blade and table for lower counts
        mod = mod * abs(tturn_max/tturn_speed)
    print(round(mod,2),end='')
    tturn_speed = tturn_speed*mod
    pep_speed = pep_speed*mod

    
    translate=threading.Thread(target=ttran.step,args=(in2step(row_ct[0]),24000))
    rotate=threading.Thread(target=tturn.ramp,args=(tturn_speed,))
    #lift = threading.Thread(target=tlift.step,args=(-lift_steps,8000,))
    translate.start()
    rotate.start()
    #lift.start()
    translate.join()
    #start slicing, count first pep;
    GPIO.add_event_detect(hall_pin,GPIO.FALLING,callback=hallblip,bouncetime=round(800/pps))
    pep.turn(pep_speed)
    rotate.join()
    n = 0 #peps per row on interrupt
    k = n #total peps on pizza compiled at end of loop
    
    print('\t [',end='')
    for i in range(len(pep_ct)): #the business end
        try:
            if i and GPIO.input(lim_pin): #prevent duplicate initial index and overlimit movement
                translate=threading.Thread(target=ttran.step,args=(in2step(row_ct[i]),12000,))
                translate.start()
            if pep_ct[i]>1:
                
                tturn_steps = int(tturn_ratio * (1 - .25 * 2**(-i))) #rotate table 1 pep width less than 1 rev
                tturn_speed = 2*pps*tturn_steps/pep_ct[i] #fit x peps in that section, assuming bladespeed of pps
                pep_speed = pps*pep_ratio #calculate how fast to rotate blade
                
                mod = 1  # default no mod multiplier
                if abs(tturn_speed) > tturn_max: #slow down blade and table for lower counts
                    mod = mod * abs(tturn_max/tturn_speed)
                    print('t',end='')
                if pep_speed > pep_max:
                    mod = mod * abs(pep_max/pep_speed)
                    print('p',end='')
                tturn_speed = tturn_speed*mod
                pep_speed = pep_speed*mod
                tturn.stop() #end previous tturn.turn to start tturn.step thread
                
                rotate=threading.Thread(target=tturn.step,args=(tturn_steps,tturn_speed,))
                slicer=threading.Thread(target=pep.turn,args=(pep_speed,))
                rotate.start()
                slicer.start()
                
                while rotate.is_alive():
                    if shutdown:raise Exception('shutdown')
                    time.sleep(.01) #allow time for threads
                tturn.turn(tturn_speed)
                
            print(n, end=', ', flush=True)
            k += n #compile total pep count
            n=0 #move to new row and reset counter
            while n==0:pass #wait for encoder to trigger before moving on
        except Exception as e:
            print(e,end='')
            break
    print(n,k,']',end='  ')
    
    #stop and clean up
    stop()
    #tlift.step(lift_steps,8000)
    home()
    stop()
    cycletime=round(time.time()-pizzaTime,2)
    print(cycletime,'sec')
    
    global algimg
    algimg.destroy()
    


#***********************UIFunctions******************************#
from tkinter import *
root=Tk() #Create a window

bold=font.Font(family='Helvetica', size=50, weight='bold')
font=font.Font(family='Helvetica', size=20, weight='normal')
preset={1:{'name':'7\nFull','size':7,'qty':25},
        2:{'name':'10\nFull','size':10,'qty':48},
        3:{'name':'12\nFull','size':12,'qty':75},
        4:{'name':'14\nFull','size':14,'qty':101},
        5:{'name':'7\nLess','size':7,'qty':16},
        6:{'name':'10\nLess','size':10,'qty':31},
        7:{'name':'12\nLess','size':12,'qty':46},
        8:{'name':'14\nLess','size':14,'qty':61},}

def killscreen():   #Program kills main window
    root.destroy()
def homescreen():
    root.overrideredirect(1) #Full screen if uncommented
    root.geometry('640x480')
    root.title("Sm^rt Pep")
    namelabel=Label(root, text="Welcome to   SM^RT PEPP   by Agàpe Automation", font=font).place(x=75,y=0)

    fnoption=[None]*9
    fnoption[1]=Button(root,text=preset[1]['name'],font=bold,bg='green',fg='white',command=lambda:run_pep(preset[1]['size'],preset[1]['qty']),height=2,width=3)
    fnoption[2]=Button(root,text=preset[2]['name'],font=bold,bg='green',fg='white',command=lambda:run_pep(preset[2]['size'],preset[2]['qty']),height=2,width=3)
    fnoption[3]=Button(root,text=preset[3]['name'],font=bold,bg='green',fg='white',command=lambda:run_pep(preset[3]['size'],preset[3]['qty']),height=2,width=3)
    fnoption[4]=Button(root,text=preset[4]['name'],font=bold,bg='green',fg='white',command=lambda:run_pep(preset[4]['size'],preset[4]['qty']),height=2,width=3)
    fnoption[5]=Button(root,text=preset[5]['name'],font=bold,bg='green',fg='white',command=lambda:run_pep(preset[5]['size'],preset[5]['qty']),height=2,width=3)
    fnoption[6]=Button(root,text=preset[6]['name'],font=bold,bg='green',fg='white',command=lambda:run_pep(preset[6]['size'],preset[6]['qty']),height=2,width=3)
    fnoption[7]=Button(root,text=preset[7]['name'],font=bold,bg='green',fg='white',command=lambda:run_pep(preset[7]['size'],preset[7]['qty']),height=2,width=3)
    fnoption[8]=Button(root,text=preset[8]['name'],font=bold,bg='green',fg='white',command=lambda:run_pep(preset[8]['size'],preset[8]['qty']),height=2,width=3)
    fnlocx=[None]+[30,180,330,480]*2
    fnlocy=[None]+[40]*4+[220]*4
    for i in range(1,len(fnoption)):              
        fnoption[i].place(x=fnlocx[i],y=fnlocy[i])
    fnedit=Button(root,text='EDIT',font=font,command=fn_edit1,height=2,width=10).place(x=500,y=400)
    Button(root, text="X", font=font,bg="red", fg="white", command=killscreen,height=1, width=1).place(x=0,y=0)
    Button(root,text="HOME",font=font,command=home,height=2,width=10).place(x=100,y=400)
    Button(root,text="STOP",font=font,bg="red",fg="white",command=stop,height=2,width=10).place(x=300,y=400)

def fn_edit1():
    global fnedit1
    global n
    fnedit1=Toplevel(root)
    fnedit1.overrideredirect(1)
    fnedit1.geometry('640x480')
    Label(fnedit1, text='Select which preset to edit:', font=font).place(x=75,y=0)                
    fnoption=[None]*9
    fnlocx=[None]+[30,180,330,480]*2
    fnlocy=[None]+[40]*4+[220]*4
    for i in range(1,len(fnoption)):
        fnoption[i]=Button(fnedit1,text=preset[i]['name'],font=bold,bg='green',fg='white',command=lambda:fn_edit2(i),height=2,width=4)
        fnoption[i].place(x=fnlocx[i],y=fnlocy[i])
    print(dir(fnoption[1]))
    Button(fnedit1,text='BACK',font=font,command=fnedit1.destroy,height=2,width=10).place(x=500,y=400)
    Button(fnedit1, text="X", font=font,bg="red", fg="white", command=killscreen,height=1, width=1).place(x=0, y=0)
def fn_edit2(m):
    global fnedit2
    fnedit2=Toplevel(fnedit1)
    fnedit2.overrideredirect(1)
    fnedit2.geometry('640x480')
    Label(fnedit2, text='Edit parameters for:', font=font).place(x=75,y=10) 
    Button(fnedit2,text=preset[m]['name'],font=font,bg='green',fg='white',height=4,width=10).place(x=100,y=50)
    
    Label(fnedit2, text='_Pepp Quantity:', font=font).place(x=300,y=120)  
    qbox=Spinbox(fnedit2,from_=5,to=150,increment=1,font=bold,width=3,command=lambda:fn_edit3(m,'qty',qbox.get()))
    qbox.delete(0,'end')
    qbox.insert(0,str(preset[m]['qty']))
    qbox.place(x=500,y=100)
    
    Label(fnedit2, text='____Pizza Size:', font=font).place(x=300,y=220)
    sbox=Spinbox(fnedit2,values=[7,10,12,14],font=bold,wrap=True,width=3,command=lambda:fn_edit3(m,'size',sbox.get()))
    sbox.delete(0,'end')
    sbox.insert(0,str(preset[m]['size']))
    sbox.place(x=500,y=200)
    
    Label(fnedit2, text='__Crust Margin:', font=font).place(x=300,y=320)
    mbox=Spinbox(fnedit2,from_=0,to=3,increment=.1,font=bold,wrap=True,width=3,command=lambda:fn_edit3(m,'size',sbox.get()))
    mbox.delete(0,'end')
    mbox.insert(0,str(preset[m]['size']))
    mbox.place(x=500,y=200)
    
    Button(fnedit2,text='BACK',font=font,command=fnedit2.destroy,height=2,width=10).place(x=500,y=400)
    Button(fnedit2, text="X", font=font,bg="red", fg="white", command=killscreen,height=1, width=1).place(x=0, y=0)
def fn_edit3(m,n,amt):
    preset[m][n]=int(amt)

homescreen()
root.mainloop()        