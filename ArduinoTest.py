from InstPyr.Interfaces.Arduino.myarduino import myarduino
import time

arduino = myarduino('COM4')
arduino.initializeIO(ain=[0])
# TODO convert the modes above to struct or typedef
counter = 0.01
rampup = True
while (True):
    a=arduino.read_analog(0)
    time.sleep(1)
    print(a)

