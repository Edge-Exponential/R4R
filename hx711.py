import RPi.GPIO as GPIO
clk_pin=11
data_pin=13
zero_init=0 #lbs offset
calib_init=.0000007916 #bits to lbs conversion
zero=zero_init
calib=calib_init

def init(cp=clk_pin,dp=data_pin):
    global clk_pin
    global data_pin
    clk_pin=cp
    data_pin=dp
    
    GPIO.setwarnings(False)
    if not GPIO.getmode(): GPIO.setmode(GPIO.BOARD)
    GPIO.setup(dp,GPIO.IN) #set HX711 data pin
    GPIO.setup(cp,GPIO.OUT) #set HX711 clock pin
    GPIO.output(cp,0) #power on HX711

    

def bits(bitlength=27): #default bit string length 27 for channel A, gain=64
    global clk_pin
    global data_pin
    b=0b0
    for i in range(bitlength): 
        GPIO.output(clk_pin,1) #clock high
        b=(b<<1)|GPIO.input(data_pin) #shift register and append new data bit
        GPIO.output(clk_pin,0) # clock low
    if b==0: print("connect HX711, use: 'init(clk_pin,data_pin)'")
    return b

def read():
    global zero
    global calib
    weight=round(bits()*calib-zero,4)
    return weight
    
def tare():
    global zero
    global calib
    zero=bits()*calib
    return zero
    
def calibrate(known_wt=1.1): #known weight can be any unit
    global calib
    try:calib=calib*known_wt/(bits()*calib-zero)
    except ZeroDivisionError: pass
    return calib
