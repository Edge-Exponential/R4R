peptest.py [v1] is a collection of object commands to control the R4R system.
	It constantly evolves as the test bench for new methods

peptest_pants.py [v2] runs the involute pep blade with high precision.
	Features include: DC blade motor, pan rotation and translation stepper motors,
	Full tkinter interface with size and pepp quantity selection
	Hall-effect encoder for overspeed e-stop, stall power ramp-up, turntable speed adjustment

peptest_v3.py [v3] runs the involute pep blade with a DC motor and PID control.
	This was an attempt to mitigate the effects of the motor slowing down under load.

peptest_v4.py [v4] runs the involute pep blade with a stepper motor and minimal feedback.
	Pepp quantity and row spacing for each size is brute-forced with arrays and dictionaries.

peptest_v5.py [v5] builds on v4 with an pepperoni position algorithm.
	Generates preview image and position arrays based on quantity and crust dimensions.
	
peptest_v6.py [v6] replaces blademotor clock signal with serial command.
	Arduino receives message and generates cleaner clock signal.
	
peptest_v7.py [v7] cleans up UI and fully integrates lifter to pep cycle.
	Removed settings screen.
	
chztest.py runs an auger stepper, turntable stepper, and load cell for PID control.
	Vibrating conveyor control via relay

stepper.py is a custom portable library to run stepper motors.

mag_sensor.py [archived] Hall-effect encoder interrupt program
