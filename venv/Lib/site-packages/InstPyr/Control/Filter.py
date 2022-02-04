import scipy.signal as signal
import numpy as np
from ..Utilities.shiftregister import shiftregister
import time
class MyFilter:
    def __init__(self):
        self.lowpassfilt=None

    @classmethod
    def lowpass(cls,data,cutoff, sampling):
        # if self.lowpassfilt==None:
        # b, a = signal.butter(10,cutoff,fs=sampling)
        b,a=signal.butter(10,cutoff,fs=sampling)
        # print(data)
        # print(b)
        # print(a)
        y=signal.filtfilt(b,a,data)
        # print(y)
        yout=y[len(y)-1]
        # # print(b)
        # newval=signal.filtfilt(b,a,data,padlen=0)
        # print(newval)
        # return newval[len(newval)-1]
        #TODO figure out how lowpass filtering works
        return yout

    @classmethod
    def movingaverage(cls,data,N=0):
        #sampling rate in seconds
        if N==0 or N>len(data):
            return np.average(data)
        else:
            return np.average(data[len(data)-N:len(data)-1])

    # @classmethod
    # # def rampfilter(cls,data,rate):

class RateLimiter(MyFilter):
    def __init__(self,ratelimit):
        super().__init__()
        self.output=0
        self.rate=ratelimit
        self.maxrate=ratelimit
        self.currentTime=time.time()
        self.registersize=10
        self.buffer=shiftregister(self.registersize)

    def nextVal(self,data):
        self.buffer.push(data)
        self.newtime=time.time()
        elapsedtime=self.newtime-self.currentTime
        #read last two values:
        list=self.buffer.showlast(2)
        if elapsedtime!=0:
            rate=(list[1]-self.output)/elapsedtime
        else:
            rate=0

        if abs(rate)<self.maxrate:
            self.rate=rate
        else:
            self.rate=np.sign(rate)*self.maxrate

        self.currentTime=self.newtime
        self.output=self.output+self.rate*elapsedtime
        return self.output




    def reset(self):
        self.output=0
        self.buffer=shiftregister(self.registersize)




