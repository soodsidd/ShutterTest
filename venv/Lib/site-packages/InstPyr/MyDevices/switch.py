from ..Interfaces.Common import interface


class switch():
    def __init__(self, interface: interface.interface, pin, voltage=5):
        self.interface=interface
        self.pin=pin
        self.voltage=voltage

        self.interface.initializeIO(dout=[self.pin])
        self.state=False
        self.interface.write_digital(self.pin,self.state)

    def setstate(self, state):
        self.state=state
        self.interface.write_digital(self.pin,self.state)
