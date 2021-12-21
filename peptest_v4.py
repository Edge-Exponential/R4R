import RPi.GPIO as GPIO
import time
import stepper
import threading

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

def in2step(inch):
    return int(inch*200*8/(3.14159*.411)) #Convert distance to steps on motor
def home():
    ttran.turn(12000)
    while GPIO.input(lim_pin):pass
    ttran.stop()
def hallblip(x):
    global n
    n+=1
GPIO.add_event_detect(hall_pin,GPIO.FALLING,callback=hallblip,bouncetime=100)
def demo(size,r4r=True,pps=3):#peps/sec changes speed of the whole script
    t0=time.time() #start timer
    global n #interrupt counter global var

#Parameters
    pep_ratio=800*1.11 #steps/bladerev
    table_ratio=400     #steps/tablerev
    if r4r: #Ready-for-Revenue Pep
        pep_ct={14:[5,12,18,25],
                12:[4,11,17,24],
                10:[1,6,9,15],
                7: [1,6,9]}
        row_ct={14:[-4.8,1.5,1.5,1.6], 
                12:[1.0,1.28,1.09,1.61,1.31],
                10:[-5.6,1.45,1.45,1.45],
                7: [-5.6,1.45,1.45]}
    else: #Full Pep
        pep_ct={14:[3,9,14,21,26,32],
                12:[3,9,14,21,26],
                10:[4,9,16,23],
                7: []}
        row_ct={14:[-5.3,1.12,1.12,1.12,1.12,1.12],
                12:[-5.3,1.12,1.12,1.12,1.12],
                10:[2.0,1.15,1.15,1.15],
                7: []}
#Script   
    home()
    translate=threading.Thread(target=ttran.step,args=(in2step(row_ct[size][0]),24000,))
    if pep_ct[size][0]<4: #slow down blade and table for lower counts
        rotate=threading.Thread(target=tturn.ramp,args=(pps*table_ratio/pep_ct[size][1],))
    else: rotate=threading.Thread(target=tturn.ramp,args=(pps*table_ratio/pep_ct[size][0],))
    translate.start()
    rotate.start()
    translate.join()
    rotate.join()
    n=0
    pep.ramp(pps*pep_ratio,.5)
    
    
    for i in range(len(pep_ct[size])): #the business end
        if i: #prevent duplicate initial index movement   
            translate=threading.Thread(target=ttran.step,args=(in2step(row_ct[size][i]),24000,))
            translate.start()
            table_mod=table_ratio
            w_rot=pps*table_ratio/pep_ct[size][i]
        else:
            table_mod=table_ratio*(pep_ct[size][i]-1)/pep_ct[size][i]
            w_rot=pps*table_ratio/pep_ct[size][i+1]
        tturn.stop()
        tturn.step(table_mod,w_rot)
        tturn.turn(w_rot/2)
        print('Target: ',pep_ct[size][i],'\tCount: ',n)
        n=0
        while GPIO.input(hall_pin):pass

    stop()
    home()
    print('Time Elapsed: ',round(time.time()-t0,2),'s,',n,'extra pep')

def stop():
    pep.stop()
    tturn.stop()
    ttran.stop()