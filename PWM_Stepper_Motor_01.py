
from time import sleep
import RPi.GPIO as GPIO
#
PUL = 11  # Stepper Drive Pulses
DIR = 13  

GPIO.setmode(GPIO.BOARD)

GPIO.setup(PUL, GPIO.OUT)
GPIO.setup(DIR, GPIO.OUT)
GPIO.output(PUL, GPIO.LOW)
GPIO.output(DIR, GPIO.LOW)

print('Initialization Completed')

durationFwd = 100 # This is the duration of the motor spinning. used for forward direction
print('Duration Fwd set to ' + str(durationFwd))

delay = 1/50 # This is actualy a delay between PUL pulses - effectively sets the mtor rotation speed
print('Speed set to ' + str(delay))


for x in range(durationFwd): 
    GPIO.output(PUL, GPIO.HIGH)
    #GPIO.output(PUL, GPIO.LOW)
    sleep(delay)
    #print('Running')
    GPIO.output(PUL, GPIO.LOW)
    sleep(delay)
    x=x+1

# print('Finished')
GPIO.cleanup()

