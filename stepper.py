import RPi.GPIO as GPIO
import time        


class motor(object):
    freq=0
    def __init__(self,clkpin,dirpin):
        self.clk_pin=clkpin
        self.dir_pin=dirpin
        GPIO.setup(clkpin,GPIO.OUT)
        GPIO.setup(dirpin,GPIO.OUT)
        GPIO.output(clkpin,0)
        GPIO.output(dirpin,0)
        self.pwm=GPIO.PWM(clkpin,100)
        
    def turn(self,freq):
        GPIO.output(self.dir_pin,GPIO.LOW)
        if freq<0:
            GPIO.output(self.dir_pin,GPIO.HIGH)
            freq=-freq
        try:
            self.pwm.ChangeFrequency(freq)
            self.pwm.start(50)
            self.freq=freq
        except ValueError:
            self.pwm.start(0)
    def ramp(self,freq,dur=2):
        increment=round((freq-self.freq)/(dur*10))
        for i in range(self.freq,freq+increment,increment):
            if i<0:
                i=-i
                GPIO.output(self.dir_pin,GPIO.HIGH)
            else: GPIO.output(self.dir_pin,GPIO.LOW)
            try:
                self.pwm.ChangeFrequency(i)
                self.pwm.start(50)
            except ValueError:
                self.pwm.start(0)
            time.sleep(dur/10)
        self.freq=freq
    def step(self,steps,freq):
        GPIO.output(self.dir_pin,GPIO.LOW)
        if freq<0:
            GPIO.output(self.dir_pin,GPIO.HIGH)
            freq=-freq
        self.freq=freq
        for i in range(steps):
            GPIO.output(self.clk_pin,1)
            time.sleep(1/freq)
            GPIO.output(self.clk_pin,0)
            time.sleep(1/freq)
        self.freq=0
    def stop(self):
        self.pwm.stop()
        self.freq=0
