import RPi.GPIO as GPIO
import time        

class motor(object):
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
        except ValueError:
            self.pwm.start(0)
        
    def stop(self):
        self.pwm.start(0)
