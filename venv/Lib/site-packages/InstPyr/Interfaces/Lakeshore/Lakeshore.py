from ..Common.interface import interface
import serial

class Lakeshore(interface):
    def __init__(self, COMport):
        super().__init__(self)
        self.comport=COMport
        try:
            self.dev_conn = serial.Serial(port=self.comport,
                                          baudrate=9600,
                                          xonxoff=False,
                                          parity=serial.PARITY_ODD,
                                          bytesize=serial.SEVENBITS,
                                          stopbits=serial.STOPBITS_ONE,
                                          timeout=2.0,
                                          rtscts=False)
        except Exception:
            print('Could not connect to lakeshore')
            self.dev_conn = None

        print(self._query('*IDN?'))
        # self.currentTemp = self.readTemperature()

    def _query(self, command):
        self.dev_conn.write(command.encode('ascii') + b'\n')
        return self.dev_conn.readline().decode('ascii')

    def readTemperature(self, channel):
        self.currentTemp = float(self._query('CRDG? {}'.format(channel)))
        return self.currentTemp

    def close(self):
        self.dev_conn.close()
