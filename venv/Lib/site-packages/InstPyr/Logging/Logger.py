import csv
from datetime import datetime
import time
import os

class Logger():
    def __init__(self,fname,headers,mode,timestamped=True):
        self.fname=fname
        if os.path.exists(fname) and mode !='a':
            raise Exception

        self.file=open(fname,mode)
        #write headers to the file
        self.writer=csv.writer(self.file,lineterminator='\n')
        # print(self.file)
        # print(headers)
        if mode != 'a':
            if timestamped==True:
                header=['Time']
                header+=headers
                self.writer.writerow(header)
        # self.fname.close()
        # self.fname=open(fname,'a+')


    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.file.close()

    def close(self):
        self.file.close()

    def writedata(self,data):
        self.writer.writerow(data)

    def writetimedata(self,data):
        data[0]=data[0].strftime('%Y-%m-%d %H:%M:%S')
        self.writer.writerow(data)

    def clearfile(self):
        self.file.truncate(0)

if __name__=="__main__":
    logger=Logger('C:\\Users\\soods\\Desktop\\Python\\TemperatureLogger\\data\\test.csv',['A','B','C'])
    logger.writetimedata([datetime.now(),2,3])
    logger.close()
    # with logger:
    #     for i in range(1,10):
    #
    #         logger.writetimedata([datetime.now(),2,3])
    #         time.sleep(1)
    #     #     logger.writetimedata([datetime.now(),3,4])
        # # logger.clearfile()

