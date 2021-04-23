peptest.py is a collection of object commands to control the R4R system

class pep controls the DM860T stepper driver
pep.init() creates a PWM object in Python
pep.turn(freq) spins the motor a given speed (usually 100-1500)
pep.stop() cleanly stops the motor

class table controls the translation and rotation of the platter gantry
table.init() creates a PWM object
table.turn(freq) spins the motor to a given speed (usually 100-600)
table.move(dist) cycles the belt. The whole travel is about dist=350
table.stop() cleanly stops both motors but doesn't interrupt

stop() will stop all motors
