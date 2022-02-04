import control
import numpy as np
import matplotlib.pyplot as plt
import collections


class Plant:
    def __init__(self,tf_num, tf_den):
        self.sys=control.tf(tf_num,tf_den)
        # self.t.append(0)
        # self.x.append(0)
        print(self.sys)
        self.xprev=0
        self.tprev=0


    def stepResponse(self):
        plt.close('all')
        (t,y)=control.step_response(self.sys)
        plt.plot(t,y)
        plt.show()

    def impulseResponse(self):
        plt.close('all')
        (t,y)=control.impulse_response(self.sys)
        plt.plot(t,y)
        plt.show()


    def realTime(self,xin,tin):
        if tin!=0:
            dt=tin-self.tprev
            t_temp,y_temp,x_temp=control.forced_response(self.sys,[self.tprev,tin],[xin,xin],X0=self.xprev,return_x=True)
            yout=np.squeeze(y_temp[-1])
            self.xprev=np.squeeze(x_temp[:,-1])
            self.tprev=tin

        else:
            yout=0
        return yout

if __name__=='__main__':
    import Noise
    s=Plant([1],[1,0.5,1])
    # s.stepResponse()
    nt=1000
    x=np.zeros(nt)
    x[int(0.1*nt):int(0.95*nt)]=1
    t=np.linspace(1,500,nt)
    y=[]
    for i in range(len(x)):
        # print(i)
        out=s.realTime(x[i],t[i])
        # out+=next(Noise.Noise.generate(0.1))
        y.append(out)

    plt.plot(t,y)
    plt.plot(t,x)
    plt.show()