import RPi.GPIO as GPIO
import time
import stepper
import threading
import math

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
lim_pin=18
hall_pin=12
n=0
GPIO.setup(lim_pin,GPIO.IN, pull_up_down=GPIO.PUD_UP) #limit switch 
GPIO.setup(hall_pin,GPIO.IN, pull_up_down=GPIO.PUD_UP) #blade encoder

pep=stepper.motor(36,35)
tturn=stepper.motor(11,15)
ttran=stepper.motor(33,29)

pep_ratio=800*14/18  #steps/bladerev
ttran_ratio=3200    #setps/transrev
tturn_ratio=200*8     #steps/tablerev

def in2step(inch):
    return int(inch*ttran_ratio/(3.14159*.902)) #Convert distance to steps on motor
def home():
    ttran.turn(12000)
    while GPIO.input(lim_pin): time.sleep(.03)
    ttran.stop()
def hallblip(x):
    global n
    n+=1
GPIO.add_event_detect(hall_pin,GPIO.FALLING,callback=hallblip,bouncetime=600)
def demo(size=10,qty=0,pps=3,margin=1.6,center=-5.6):#pps changes speed of the whole script
    t0=time.time() #start timer
    global n #interrupt counter global var
    rpep=.7 #mm
#Parameters
    if qty>1:
        r=(size-margin-rpep)/2
        dr=math.sqrt(math.pi*r*r/(0.0003172*qty*qty+.8365*qty-3.9))
        nr=math.ceil(r/dr)
        print(r,dr,nr)
        row_ct=[dr]*nr
        row_ct[0]=center+r-(nr-1)*dr
        pep_ct=[]  
        for m in range(nr):
            pep_ct.append(round((r-m*dr)*2*math.pi/dr))
        if pep_ct[-1]==0:pep_ct[-1]=1
        if pep_ct[-1]>4:pep_ct.append(1)
        pep_ct.reverse()
    elif qty: #Full Pep
        if size==14:
            pep_ct=[3,9,14,21,26,32]
            row_ct=[-5.3,1.12,1.12,1.12,1.12,1.12]
        if size==12:
            pep_ct=[3,9,14,21,26]
            row_ct=[-5.3,1.12,1.12,1.12,1.12]
        if size==10:
            pep_ct=[23,16,9,4]
            row_ct=[2.0,1.15,1.15,1.15]
        if size==7:
            pep_ct=[]
            row_ct=[]
    else: #Ready-for-Revenue Pep
        if size==14:
            pep_ct=[5,12,18,25]
            row_ct=[-4.8,1.5,1.5,1.6]
        if size==12:
            pep_ct=[1,4,9,15]
            row_ct=[-5.6,1.7,1.7,1.7]
        if size==10:
            pep_ct=[1,4,9,15]
            row_ct=[-5.6,1.55,1.45,1.43]
        if size==7:
            pep_ct=[1,6,9]
            row_ct=[-5.6,1.45,1.45]
    print(pep_ct,row_ct)

#Script   
    home()
    translate=threading.Thread(target=ttran.step,args=(in2step(row_ct[0]),24000))
    if pep_ct[0]<4: #slow down blade and table for lower counts
        rotate=threading.Thread(target=tturn.ramp,args=(pps*tturn_ratio/pep_ct[1],))
    else: rotate=threading.Thread(target=tturn.ramp,args=(pps*tturn_ratio/pep_ct[0],))
    translate.start()
    rotate.start()
    translate.join()
    rotate.join()
    n=1
    pep.ramp(pps*pep_ratio,.5)
    
    print('[',end='')
    for i in range(len(pep_ct)): #the business end
        try:
            if i: #prevent duplicate initial index movement   
                translate=threading.Thread(target=ttran.step,args=(in2step(row_ct[i]),24000,))
                translate.start()
            if pep_ct[i]>1:
                w_rot=pps*tturn_ratio/pep_ct[i]
                tturn.stop()
                tturn.step(.95*tturn_ratio,w_rot)
                tturn.turn(w_rot/2)
            print(n,' ',end='',flush=True)
            n=0
            m=0
            while m==n:pass
        except:
            print('error')
            break
    print(n,']',end='  ')
    stop()
    home()
    print(round(time.time()-t0,2),'sec')
def half(size=10,qty=0,pps=3):
    t0=time.time() #start timer
    global n #interrupt counter global var
    pep_ct={14:[1,4,7,10,13,16],
            10:[3,6,9]}
    row_ct={14:[-5.3,1.12,1.12,1.12,1.12,1.12],
            10:[-5.6,1.5,1.5,1.6]}
    home()
    translate=threading.Thread(target=ttran.step,args=(in2step(row_ct[size][0]),24000))
    if pep_ct[size][0]<4: #slow down blade and table for lower counts
        rotate=threading.Thread(target=tturn.ramp,args=(pps*tturn_ratio/pep_ct[size][1],))
    else: rotate=threading.Thread(target=tturn.ramp,args=(pps*tturn_ratio/pep_ct[size][0],))
    translate.start()
    rotate.start()
    translate.join()
    rotate.join()
    n=1
    tturnrev=1
    pep.ramp(pps*pep_ratio,.5)
    
    for i in range(len(pep_ct[size])): #the business end
        if i: #prevent duplicate initial index movement   
            translate=threading.Thread(target=ttran.step,args=(in2step(row_ct[size][i]),24000,))
            translate.start()
        if pep_ct[size][i]>1:
            w_rot=pps*tturn_ratio/pep_ct[size][i]
            tturn.stop()
            tturnrev=-tturnrev
            tturn.step(.5*tturn_ratio*tturnrev,w_rot)
            tturn.turn(w_rot*tturnrev/2)
        print('Target: ',pep_ct[size][i],'\tCount: ',n)
        n=0
        m=0
        while m==n:pass
    stop()
    home()
    print('Time Elapsed: ',round(time.time()-t0,2),'s,',n,'extra pep')
    
def stop():
    pep.stop()
    tturn.stop()
    ttran.stop()

        