import collections

import numpy as np
import matplotlib.pyplot as plt
#TODO- make parent class

class triangle:
    def __init__(self,sample:float,period:float,maxval=1,minval=0,duty=0.5):
        self.sample_num = (int)(period / sample)
        self.signal = []
        self.currentindex = 0
        firstperiod=(int)(duty*self.sample_num)+1
        firstSet=np.linspace(minval,maxval,firstperiod)
        secondperiod=self.sample_num-firstperiod+2
        secondSet=np.linspace(maxval,minval,secondperiod)
        for i in range(self.sample_num+2):
            if i < firstperiod:
                self.signal += [firstSet[i]]
            else:
                if i==firstperiod:
                    self.signal[firstperiod-1]=secondSet[i-firstperiod]
                else:
                    self.signal += [secondSet[i-firstperiod]]

    def nextval(self):
        out = self.signal[self.currentindex]
        self.currentindex += 1
        if self.currentindex >= self.sample_num:
            self.currentindex = 0
        return out

    def __len__(self):
        return len(self.signal)

    def __str__(self):
        return str(self.signal)

class sinusoid:
    pass

class square:
    def __init__(self,sample:float,period:float,maxval=1,minval=0,duty=0.5 ):
        #initialize waveform here
        self.sample_num=(int)(period/sample)
        self.signal=[]
        self.midsample=duty*self.sample_num
        self.currentindex=0
        for i in range(self.sample_num):
            if i>self.midsample:
                self.signal+=[minval]
            else:
                self.signal+=[maxval]

    def nextval(self):
        out=self.signal[self.currentindex]
        self.currentindex+=1
        if self.currentindex>=self.sample_num:
            self.currentindex=0
        return out

    def __len__(self):
        return len(self.signal)

    def __str__(self):
        return str(self.signal)

if __name__=="__main__":
    squarewave=square(0.25,1)
    trianglewave=triangle(0.1,19*0.1,duty=0.7)
    print(squarewave)
    a=len(trianglewave)
    print(a)
    array=[]
    for i in range(3*a):
        print(i)
        # print(trianglewave.nextval())
        array.append(trianglewave.nextval())

    print(array)

    plt.plot(array)
    plt.show()


