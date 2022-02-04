import pyfirmata
import time

board=pyfirmata.Arduino('COM3')
it=pyfirmata.util.Iterator(board)
it.start()

board.digital[13].mode=1
board.analog[1].enable_reporting()

while True:

    # sw=board.digital[7].read()
    # if sw is True:
    #     board.digital[13].write(1)
    # else:
    #     board.digital[13].write(0)
    # time.sleep(0.1)
    print(board.analog[1].read())
    board.digital[13].write(1)
    time.sleep(0.5)
    board.digital[13].write(0)
    time.sleep(0.5)