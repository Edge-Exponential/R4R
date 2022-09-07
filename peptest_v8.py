_version = 'b.8.3'
filepath = '/home/pi/Desktop/'
import RPi.GPIO as GPIO
import time
import stepper
import threading
import math
import serial
import json
import PIL.Image,PIL.ImageDraw,PIL.ImageTk
from tkinter import *

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# INPUTS
lim_pin=32 #gantry limit switch
low_pin=29 #lifter limit switch
hm_pin=36 #blade shaft encoder (1 blip per rev)
ht_pin=38  #hall top, tube sensor
ir_pin=40  #infrared pepperoni sensor
GPIO.setup(lim_pin,GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(low_pin,GPIO.IN, pull_up_down=GPIO.PUD_UP) 
GPIO.setup(hm_pin,GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ht_pin,GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ir_pin,GPIO.IN, pull_up_down=GPIO.PUD_UP)

# OUTPUTS (see further down for pep motor output)
ena_pin=16 #stepper motor enable, 1=disable to keep temps down
GPIO.setup(ena_pin,GPIO.OUT)
#example: stepper.motor(PUL,DIR)
# tturn=stepper.motor(7,11)
# ttran=stepper.motor(13,15)
# tlift=stepper.motor(38,40)
tturn=stepper.motor(26,11)
ttran=stepper.motor(18,3)
tlift=stepper.motor(24,7)

# MECHANICAL PARAMETERS
pep_ratio = -3200 # * .6 #*14/19  #steps/bladerev
pep_max = 10000 #blade top speed Hz --- Arduino can only smoothly ramp up to 2kHz and maxes out at 12.5kHz with pep.turn(500000)
ttran_ratio = 1600/(1.273*3.1415)    #steps/transinch
ttran_max = abs(3 * ttran_ratio)
tturn_ratio = 1600    #steps/tablerev
tturn_max = .8*tturn_ratio #turntable top speed Hz
tlift_ratio = -400/(8/25.4)  #steps/in (8mm screw lead)
tlift_max = 1.5 #inch extension

n = 0
shutdown = False

try: #connect to arduino and define serial comm functions
    ser = serial.Serial("/dev/ttyACM0",9600,writeTimeout=3)
    GPIO.setup(37,GPIO.OUT)
    class pep:
        freq = 0
        def stop():
            ser.write(b'0\r\n')
            pep.freq=0
        def turn(freq):
            GPIO.output(37,0)
            if freq == 0:
                pep.stop()
                return
            elif freq < 0:
                GPIO.output(37,1)
                freq=-freq
            freq = int(500000/(freq))-1
            ser.write(b'%d\r\n' % freq)
            pep.freq=freq
    print('serial to Arduino')
except: #backup, run on pi signal with stepper.py library
    pep=stepper.motor(35,37)
    print('stepper.motor')
    
#**********************InformationFunctions******************************#
    
def read_info_file():
    global info
    try:
        with open(filepath +'pepinfo.json', 'r') as reader:
            info = json.load(reader)
    except FileNotFoundError:
        print('new info file at '+filepath+'pepinfo.json')
        info = {'slices': 0,'bladeslices':0, 'pps':4, 'pepdiam':1.3, 'center':-7.0, 'presets':{
                1:{'size':7, 'qty':[25,16,9], 'lift':[0,.5,.7],  'margin':.3},
                2:{'size':10, 'qty':[48,31,17], 'lift':[0,.3,.5],'margin':.3},
                3:{'size':12, 'qty':[75,46,29], 'lift':[0,.2,.4],'margin':.3},
                4:{'size':14, 'qty':[102,61,41], 'lift':[0,0,0], 'margin':.3}}                    
                }
        with open(filepath + 'pepinfo.json', 'w+') as writer:
            json.dump(info, writer)
        
read_info_file()
print(info)

def write_info_file():
    with open(filepath + 'pepinfo.json', 'w+') as writer:
        json.dump(info, writer)

#***********************MechanicalFunctions******************************#   
def in2step(inches):
    return int(inches*ttran_ratio) #Convert distance to steps on motor
def song():
    pass
        
def home(advancedhome=False):
    GPIO.output(ena_pin,GPIO.LOW)
    
    if advancedhome: #if bool arg is True, home lifter
        tlift.turn(-tlift_ratio)
        while GPIO.input(low_pin): time.sleep(.03)
        tlift.stop()
    
    if not GPIO.input(lim_pin): #home gantry. if already home, move out and back in
        ttran.step(int(ttran_ratio),-5*ttran_ratio)
    ttran.turn(3*ttran_ratio)
    while GPIO.input(lim_pin): time.sleep(.03)
    ttran.stop()
    
#     if advancedhome: #if bool arg is True, home blade (complete slice)
#         pep.turn(pep_ratio)
#         while GPIO.input(hm_pin): time.sleep(.03)
#         pep.stop()
    

def hallblip(x):
    global n
    n+=1
    print('|',end='')
    
def centercal(center=-7.0):
    enable()
    ttran.accel(in2step(center),12000,.25)
    pep.turn(pep_ratio)
    time.sleep(2.5)
    pep.stop()
    home()
    stop()
    
def enable():
    GPIO.output(ena_pin,GPIO.LOW)
    
def stop():
    global shutdown
    shutdown=1
    GPIO.output(ena_pin,GPIO.HIGH)
    pep.stop()
    tturn.stop()
    ttran.stop()
    tlift.stop()
    GPIO.remove_event_detect(hm_pin)
    try: pizzadisplay.place_forget()
    except: pass
#     try:
#         for window in root.winfo_children():
#             window.destroy()
#         homescreen()
#     except Exception as e: print(' and returned to home screen but',e)

def bulkslice(rpm=130):
    global shutdown
    global n
    global bulk_button
    shutdown = 0
    n=0
    bulk_tran=[0]
    bulk_button.config(bg='orange', activebackground='orange', #set translation speed if BULK button is pressed again
        command=lambda: bulk_tran.append(ttran_ratio))
    freq=int(rpm*2*pep_ratio/60)
    home()
    GPIO.add_event_detect(hm_pin,GPIO.FALLING,callback=hallblip,bouncetime=round(300*60/rpm)) #start encoder count
    pep.turn(freq) #start blade
    i=39
    while not shutdown:
        ttran.turn(bulk_tran[-1]) #start translating
        while i<40: #duration of translation in one direction ~= i*.1 seconds
            if bulk_tran[-1]:
                i+=1
            if shutdown:
                print('shutdown=',shutdown)
                pep.stop()
                ttran.stop()
                break
            if GPIO.input(ir_pin):
                print('shutdown= need pep!')
                pep.stop()
                ttran.stop()
                while GPIO.input(ir_pin): #wait for more pep
                    time.sleep(.5)
                    if shutdown: break
                if shutdown: break
                pep.turn(freq)
                ttran.turn(bulk_tran[-1])
            time.sleep(.1) #allow time for threads
        if shutdown:
            stop()
            break
        bulk_tran[-1]=-bulk_tran[-1] #reverse direction
        i=0
    stop()
    bulk_button.config(bg='gray85',activebackground='white', #replace BULK button original settings
        command=lambda: threading.Thread(target=bulkslice).start())
    info['slices']+=n #write slice count to file
    info['bladeslices']+=n
    write_info_file()
    print('bulk=',n,', blade=',info['slices'],'lifetime=',info['bladeslices'])
    
def run_pep(size=7, qty=15, lift=0, pps=4.0, margin=.3, center=-7.0, rpep=17): #pps was 4
    if GPIO.input(ht_pin): #if no tube
        cancel_var=[0]
        err1 = Tk()
        err1.wm_title('ERROR')
        Label(err1, text ='ERROR: Tube attachment required!',font=bold).pack(padx=50,pady=30)
        ignore=Button(err1,text='IGNORE',command=err1.destroy,font=bold,bg='red',padx=50,pady=30)
        ignore.pack()
        Button(err1,text='CANCEL',command=lambda: [err1.destroy(),cancel_var.append(True)],font=bold,padx=50,pady=30).pack()
        ignore.wait_window(ignore)
        if cancel_var[-1]:
            return
        
    if GPIO.input(ir_pin): #if no pep
        cancel_var=[0]
        err2 = Tk()
        err2.wm_title('ERROR')
        Label(err2, text ='ERROR: More pepperoni required!',font=bold).pack(padx=50,pady=30)
        ignore=Button(err2,text='IGNORE',command=err2.destroy,font=bold,bg='red',padx=50,pady=30)
        ignore.pack()
        Button(err2,text='CANCEL',command=lambda: [err2.destroy(),cancel_var.append(True)],font=bold,padx=50,pady=30).pack()
        ignore.wait_window(ignore)
        if cancel_var[-1]:
            return
    #create pizza mockup image then run motors pep_program in thread
    
    #calculate pep pitch circle radius in mm
    r=(size/2-margin)*25.4-rpep
    
    #image dimensions/setup
    xdim=400
    ydim=90
    im=PIL.Image.new('RGB',(xdim*2,ydim*2),(215,215,215))
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
    global algim
    algim=PIL.ImageTk.PhotoImage(im)
    global pizzadisplay
    pizzadisplay = Label(root,image=algim)
    pizzadisplay.place(x=0,y=0)
    lift_steps = int(lift * tlift_ratio)
    
    #run pep_program with e-stop capability
    print('run_pep:',pep_ct,row_ct, 'pps=',pps,', tlift=',lift_steps,end='')
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
    print(', speed modifier=',round(mod,2))
    tturn_speed = tturn_speed*mod
    pep_speed = pep_speed*mod
    
    
    GPIO.add_event_detect(hm_pin,GPIO.FALLING,callback=hallblip,bouncetime=round(800/pps))
    translate=threading.Thread(target=ttran.accel,args=(in2step(row_ct[0]),24000,1))
    rotate=threading.Thread(target=tturn.ramp,args=(tturn_speed,))
    lift = threading.Thread(target=tlift.step,args=(lift_steps,10000,))
    translate.start()
    rotate.start()
    lift.start()
    translate.join()
    
    if shutdown:
        stop()
        return
    # start slicing, count first pep;
    pep.turn(pep_speed)
    rotate.join()
    n = 0 #peps per row on interrupt
    k = n #total peps on pizza compiled at end of loop
    time.sleep(.3) #wait for first slice(s)
    
    for i in range(len(pep_ct)): #the business end
        try:
            if i and GPIO.input(lim_pin): #move to next row, but prevent duplicate initial index and overlimit movement
                translate=threading.Thread(target=ttran.accel,args=(in2step(row_ct[i]),12000,.2))
                translate.start()
            if pep_ct[i]>1:
                if i>1: #for every rows after the first two (for some reason)...
                    tturn_steps = int(tturn_ratio* (1 - .2 * 2**(-i))) #rotate table 1 pep width less than 1 rev
                else: tturn_steps = tturn_ratio
                tturn_speed = 2*pps*tturn_steps/pep_ct[i] #fit x peps in that section, assuming bladespeed of pps
                pep_speed = pps*pep_ratio #calculate how fast to rotate blade
                
                mod = 1  # default no mod multiplier
#                 if abs(tturn_speed) > tturn_max: #slow down blade and table for lower counts
#                     mod = mod * abs(tturn_max/tturn_speed)
#                     print('t',end='')
                if pep_speed > pep_max:
                    mod = mod * abs(pep_max/pep_speed)
                    print('p',end='')
                tturn_speed = int(tturn_speed*mod)
                pep_speed = int(pep_speed*mod)
#                 print("\n",mod,pep_speed)
                tturn.stop() #end previous tturn.turn to start tturn.step thread
                
                rotate=threading.Thread(target=tturn.step,args=(tturn_steps,tturn_speed,))
                rotate.start()
#                 pep.turn(pep_speed) #this makes a bunch of noise :(
                
                while rotate.is_alive():
                    if shutdown:
                        raise Exception('shutdown')
                    time.sleep(.01) #allow time for threads
                tturn.turn(tturn_speed/2)
                
            print(n,'/',pep_ct[i],flush=True)
            k += n #compile total pep count
            n=0 #move to new row and reset counter
            while n==0: #wait for encoder to trigger before moving on
                if shutdown:
                    raise Exception('shutdown')
        except Exception as e:
            print(e,end='')
            break
    if not shutdown:
        time.sleep(.25/pps)
        while GPIO.input(hm_pin):pass
    
    print(n,'total=',k,'/',sum(pep_ct),end=', ')
    
    #stop and clean up
    stop()
    enable()
    lift = threading.Thread(target=tlift.step, args=(-lift_steps,8000,))
#     lift.start()
    home(1)
    stop()
    cycletime=round(time.time()-pizzaTime,2)
    info['slices']+=k
    info['bladeslices']+=k
    write_info_file()
    print(cycletime,'sec',', blade=',info['bladeslices'],', lifetime=',info['slices'])
    if GPIO.input(ir_pin): #if no pep, diplay warning popup
        cancel_var=[0]
        err2 = Tk()
        err2.wm_title('WARNING')
        Label(err2, text ='WARNING: More pepperoni required!',font=bold).pack(padx=50,pady=30)
        ignore=Button(err2,text='OK',command=err2.destroy,font=bold,bg='red',padx=50,pady=30)
        ignore.pack()


#***********************UIFunctions******************************#

root=Tk() #Create a window
bold=font.Font(family='Helvetica', size=50, weight='bold')
norm=font.Font(family='Helvetica', size=20, weight='normal')
smol=font.Font(family='Helvetica', size=12, weight='normal')
yuge=font.Font(family='Helvetica', size=99, weight='bold')

           #name, size, quantity:[full,r4r, add], lift:[nolift,thick,thin]
preset={1:{'name':'7"','size':7, 'qty':[25,16,9], 'lift':[0,.5,.7]},
        2:{'name':'10"','size':10, 'qty':[48,31,17], 'lift':[0,.3,.5]},
        3:{'name':'12"','size':12, 'qty':[75,46,29], 'lift':[0,.2,.4]},
        4:{'name':'14"','size':14, 'qty':[102,61,41], 'lift':[0,0,0]}}

def killscreen():   #kill main window
    root.destroy()

def settingsscreen():
    setwin = Toplevel(root)
    setwin.title('SM^RT PEPP SETTINGS')
    setwin.geometry('800x480')
    navframe=Frame(setwin)
    navframe.place(x=0,y=0)
    #Label(navframe, text ='\u2699',font=bold).pack()
    backbutton=Button(navframe,text='\u2b05',command=setwin.destroy,font=bold,bg='green',fg='white')
    backbutton.pack()
    
    ttk.Style().configure('TNotebook.Tab',font=norm)
    size_tab = ttk.Notebook(setwin)
    size_tab.pack()
    frame = [Frame(size_tab,width=500,height=400),Frame(size_tab),Frame(size_tab),Frame(size_tab),Frame(size_tab),Frame(size_tab)]
    
    def reset_bladeslices():
        info['bladeslices']=0
        bladect_label.config(text='0')
        
        
    for tab in [0,1,2,3,4]: #for each size tab, populate sliders and labels
        tab_name = ['General','Preset 1','Preset 2','Preset 3','Preset 4']
        frame[tab].config(padx=30,pady=10)
        frame[tab].pack()
        size_tab.add(frame[tab],text=tab_name[tab])
        
        if tab==0: #general tab
            Label(frame[tab],text='Blade\nSpeed',font=norm).grid(row=0,column=0)
            pps_var=DoubleVar()
            pps_var.set(info['pps'])
            pps_scale=Scale(frame[tab],orient=HORIZONTAL,variable=pps_var,length=260,width=35,from_=1,to=5,resolution=0.5,tickinterval=1,showvalue=0,font=smol)
            pps_scale.grid(row=0,column=1)
            Label(frame[tab],text='slice\sec',font=norm).grid(row=0,column=2)
            
            Label(frame[tab],text='Pepperoni\nDiameter',font=norm).grid(row=1,column=0)
            pepdiam_var=DoubleVar()
            pepdiam_var.set(info['pepdiam'])
            pepdiam_scale=Scale(frame[tab],orient=HORIZONTAL,variable=pepdiam_var,length=260,width=35,from_=1,to=2,resolution=0.1,tickinterval=.5,font=smol)
            pepdiam_scale.grid(row=1,column=1)
            Label(frame[tab],text='inch',font=norm).grid(row=1,column=2)
            
            Label(frame[tab],text='Center\nDistance',font=norm).grid(row=2,column=0)
            center_var=DoubleVar()
            center_var.set(-info['center'])
            center_scale=Scale(frame[tab],orient=HORIZONTAL,variable=center_var,length=260,width=35,from_=6,to=8,resolution=0.1,tickinterval=.5,font=smol)
            center_scale.grid(row=2,column=1,padx=20)
            Label(frame[tab],text='inch',font=norm).grid(row=2,column=2)
            
            Label(frame[tab],text=' ',font=norm).grid(row=4,column=0)
            Label(frame[tab],text='Total Count:',font=norm).grid(row=6,column=0)
            Label(frame[tab],text=str(info['slices']),font=norm).grid(row=6,column=1)
            Label(frame[tab],text='Blade Count',font=norm).grid(row=7,column=0)
            bladect_label=Label(frame[tab],text=str(info['bladeslices']),font=norm)
            bladect_label.grid(row=7,column=1)
            Button(frame[tab],text='RESET',font=norm,command=reset_bladeslices,fg='white',bg='red').grid(row=6,column=2)
        
        else: #size tabs
            Label(frame[tab],text='Pan\nSize',font=norm).grid(row=0,column=0)
            pansz_var=IntVar()
            pansz_var.set(preset[tab]['size'])
            pansz_scale=Scale(frame[tab],orient=HORIZONTAL,variable=pansz_var,length=260,width=35,from_=8,to=16,resolution=2,tickinterval=2,showvalue=0,font=smol)
            pansz_scale.grid(row=0,column=1,padx=20)
            Label(frame[tab],text='inch',font=norm).grid(row=0,column=2)
            Label(frame[tab],text='7',font=smol).place(x=145,y=40)
            
            Label(frame[tab],text='Crust\nMargin',font=norm).grid(row=2,column=0)
            margin_var=DoubleVar()
            margin_var.set(.3)
            margin_scale=Scale(frame[tab],orient=HORIZONTAL,variable=margin_var,length=260,width=35,from_=0,to=2,resolution=0.1,tickinterval=.5,font=smol)
            margin_scale.grid(row=2,column=1,padx=20)
            Label(frame[tab],text='inch',font=norm).grid(row=2,column=2)
            
            Label(frame[tab],text='Full Pep\nQuantity',font=norm).grid(row=3,column=0)
            fqty_var=IntVar()
            fqty_var.set(preset[tab]['qty'][0])
            fqty_scale=Scale(frame[tab],orient=HORIZONTAL,variable=fqty_var,length=260,width=35,from_=20,to=120,resolution=1,tickinterval=50,font=smol)
            fqty_scale.grid(row=3,column=1,padx=20)
            Label(frame[tab],text='pieces',font=norm).grid(row=3,column=2)
            
            Label(frame[tab],text='R4R Pep\nQuantity',font=norm).grid(row=4,column=0)
            rqty_var=IntVar()
            rqty_var.set(preset[tab]['qty'][1])
            rqty_scale=Scale(frame[tab],orient=HORIZONTAL,variable=rqty_var,length=260,width=35,from_=10,to=70,resolution=1,tickinterval=30,font=smol)
            rqty_scale.grid(row=4,column=1,padx=20)
            Label(frame[tab],text='pieces',font=norm).grid(row=4,column=2)
        
    def write_info_dict():
        info['pps']=pps_var.get()
        info['pepdiam']=pepdiam_var.get()
        info['center']=-center_var.get()
        for i in ['1','2','3','4']:
            info['presets'][i]['size']=pansz_var.get()
            info['presets'][i]['margin']=margin_var.get()
            info['presets'][i]['qty'][0]=fqty_var.get()
            info['presets'][i]['qty'][1]=rqty_var.get()
        info['presets'][i]['qty'][2]=info['presets'][i]['qty'][0]-info['presets'][i]['qty'][1]
    
    backbutton.config(command=lambda: [write_info_dict(),write_info_file(),setwin.destroy()])
            
def homescreen():
    #root.overrideredirect(1) #Full screen if uncommented
    root.geometry('800x480') #was 800 x 648 or less
    root.title("SM^RTPEP")
    Label(root,text='SM^RTPEP | version '+_version+'\t\t\t\t\t\u00a9 Ag\u00e1pe Automation 2022').pack(side=BOTTOM)
        
#     Button(root, text="X", font=norm,bg="red", fg="white", command=killscreen,height=1, width=1).place(x=0,y=0)
    frame0=Frame(root)
       
    frame1=Frame(frame0,borderwidth=5,relief=SUNKEN) #lift setting
    lifttk=IntVar()
    lifttk.set(1)
    lifttk0=Radiobutton(frame1,text='NONE \u25bc',font=norm,variable=lifttk,value=0,indicatoron=0,width=8,height=2)
    lifttk0.pack(padx=2,pady=4) #place(x=30,y=180)
    lifttk1=Radiobutton(frame1,text='THICK \u21a5',font=norm,variable=lifttk,value=1,indicatoron=0,width=8,height=2)
    lifttk1.pack(padx=2,pady=4) #place(x=30,y=250)
    lifttk2=Radiobutton(frame1,text='THIN \u219F',font=norm,variable=lifttk,value=2,indicatoron=0,width=8,height=2)
    lifttk2.pack(padx=2,pady=4) #place(x=30,y=320)
    frame1.pack(side=LEFT,padx=5,pady=5)
    
    frame2=Frame(frame0,borderwidth=5,relief=SUNKEN) #quantity setting
    global qtytk
    qtytk=IntVar()
    qtytk0=Radiobutton(frame2,text='FULL',font=norm,variable=qtytk,value=0,indicatoron=0,width=8,height=2,command=check_fn)
    qtytk0.pack(padx=2,pady=4)
    qtytk1=Radiobutton(frame2,text='R4R',font=norm,variable=qtytk,value=1,indicatoron=0,width=8,height=2,command=check_fn)
    qtytk1.pack(padx=2,pady=4)
    qtytk2=Radiobutton(frame2,text='ADD+',font=norm,variable=qtytk,value=2,indicatoron=0,width=8,height=2,command=check_fn)
    qtytk2.pack(padx=2,pady=4)
    frame2.pack(side=LEFT,padx=5,pady=5)
    
    frame3=Frame(frame0,borderwidth=5,relief=SUNKEN) #STOP BUTTON
    Button(frame3,text="STOP",font=norm,bg="red",fg="white",command=stop,height=7,width=7,activebackground='red',activeforeground='white').pack()
    frame3.pack(side=LEFT,padx=5,pady=5)
    
    frame4=Frame(frame0,borderwidth=5,relief=SUNKEN)
    global bulk_button
    bulk_button=Button(frame4,text="\u4e96 BULK",font=norm,command=lambda: threading.Thread(target=bulkslice).start(),height=2,width=7)
    bulk_button.pack(side=TOP)
    Button(frame4,text="\u21e5 HOME",font=norm,command=lambda: [home(1),GPIO.output(ena_pin,1)],height=2,width=7).pack(side=TOP) 
    Button(frame4,text="\u2699",font=norm,command=settingsscreen,height=2,width=7).pack(side=TOP)
    frame4.pack(side=LEFT,padx=5,pady=5)
    
    qtytk.set(0)
    lifttk.set(0)
    
    frame4=Frame(root) #activate
    global fnoption
    fnoption=[None]*5
    fnlocx=[None]+[20,160,300,440]*2
    fnlocy=[None]+[10]*4+[220]*4
    for i in range(1,len(fnoption)):
        fnoption[i]=Button(frame4,text=str(preset[i]['size'])+'"',font=bold,bg='green',fg='white',height=2,width=3,
                           command=lambda i=i: run_pep(preset[i]['size'], preset[i]['qty'][qtytk.get()], preset[i]['lift'][lifttk.get()]))
        fnoption[i].pack(side=LEFT,padx=5,pady=5)
    frame4.pack(side=TOP)
    frame0.pack(side=TOP)
    
def check_fn():
    global qtytk
    global fnoption
    if qtytk.get():
        fnoption[1].config(bg='gray',state='disabled')
    else: fnoption[1].config(bg='green',state='normal')
try:
    stop()
except serial.serialutil.SerialTimeoutException:
    print('SerialTimeoutException')

homescreen()
root.mainloop()        