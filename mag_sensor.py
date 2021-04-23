import time
import datetime
from time import sleep
import RPi.GPIO as GPIO




    
PUL = 11  # Stepper Drive Pulses
DIR = 13

GPIO.setmode(GPIO.BOARD)

def sensorCallback(channel):
  # Called if sensor output changes
  timestamp = time.time()
  stamp = datetime.datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
  if GPIO.input(channel):
    # No magnet
    print("Sensor HIGH " + stamp)
    return 0
  else:
    # Magnet
    print("Sensor LOW " + stamp)
    return 1
    
# Set Switch GPIO as input
# Pull high by default
GPIO.setup(15 , GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(15, GPIO.BOTH, callback=sensorCallback, bouncetime=200)

GPIO.setup(PUL, GPIO.OUT)
GPIO.setup(DIR, GPIO.OUT)
GPIO.output(PUL, GPIO.LOW)
GPIO.output(DIR, GPIO.LOW)

print('Initialization Completed')

durationFwd = 1000
print('Duration Fwd set to ' + str(durationFwd))

delay = 1/50 # This is actualy a delay between PUL pulses - effectively sets the mtor rotation speed
print('Speed set to ' + str(delay))

global REV

REV = 0

for x in range(durationFwd): 
    GPIO.output(PUL, GPIO.HIGH)
    sleep(delay)
    GPIO.output(PUL, GPIO.LOW)
    sleep(delay)
    REV = REV + sensorCallback(15)
    x=x+1
    print(REV)
    

# print('Finished')
GPIO.cleanup()


