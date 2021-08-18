peptest.py is a collection of object commands to control the R4R system.
	It constantly evolves as the test bench for new methods

peptest_pants.py runs the involute pep blade to the highest precision possible.
	Features include: DC blade motor, pan rotation and translation stepper motors
	Hall-effect encoder for overspeed e-stop, stall power ramp-up, and turntable speed adjustment

chztest.py runs an auger stepper, turntable stepper, and load cell for PID control.
	Vibrating conveyor control has yet to be added.

stepper.py is a custom portable library to run stepper motors.

mag_sensor.py is an archived Hall-effect encoder interrupt program
