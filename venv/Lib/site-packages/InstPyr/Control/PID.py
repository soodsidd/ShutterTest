import numpy as np
from gekko import GEKKO
from scipy.signal import tf2ss
import collections
import math
import time
from dataclasses import dataclass


ATSETTLINGTIME=100
ZEROCROSSINGTOL=0.001
METHODFACTORS=[[0.5,0,0],[1/2.2,1/1.2,0],[1/1.7,1/2,1/8],[1/3.2,2.2,0],[1/2.2,2.2,6.3]]

@dataclass
class MethodList:
    ZN_P=0
    ZN_PI=1
    ZN_PID=2
    TL_PI=3
    TL_PID=4

class TuningStatus:
    COARSE_RELAY=0
    COARSE_READY=1
    COARSE_SETTLING=2
    DWELL=3
    FINE_RELAY=4
    FINE_READY=5

class PID:
    def __init__(self,Kp,Ki,Kd, out_min=-999999,out_max=999999):
        self.Kp=Kp
        self.Ki=Ki
        self.Kd=Kd
        self.limits=[out_min,out_max]
        self.outmax=out_max
        self.outmin=out_min
        self.e_prev=0
        self.t_prev=-0.001
        self.I=0
        self.P=0
        self.D=0

    def apply(self,error,t):
        self.P=self.Kp*error
        self.D=self.Kd*(error-self.e_prev)/(t-self.t_prev)
        self.e_prev = error
        self.integral(error,t)
        self.t_prev = t




        output=self.P+self.I+self.D
        return np.max([np.min([output,self.outmax]),self.outmin])

    def integral(self,error,t):
        if self.Ki!=0:
            self.Imax=(self.outmax-self.P-self.D)
            self.Imin=(self.outmin-self.P-self.D)
            change=self.Ki*error*(t-self.t_prev)
            self.I=self.I+change

            if error>0:
                if self.I>0:
                    if self.Imax>0:
                        if (self.I>self.Imax):
                            self.I=self.Imax
                    else:
                        self.I-=change

            else:
                if self.I<0:
                    if self.Imin<0:
                        if (self.I<self.Imin):
                            self.I=self.Imin
                    else:
                        self.I -= change
        else:
            self.I=0





    @classmethod
    def autotune_offline(self, tf_num, tf_den, tf, steps, amp,
                         Kc_min=0.01, Kc_max=100,
                         Ti_min=0.01, Ti_max=100,
                         Td_min=0.01, Td_max=100,
                         outmin=0, outmax=1000,
                         overshootweight=0,
                         risetimeweight=0,
                         settlingtimeweight=0):
        self.m = GEKKO()

        self.tf = tf
        self.steps = steps
        self.m.time = np.linspace(0, self.tf, self.steps)
        self.step = np.zeros(self.steps)
        self.step[0:10] = 0
        self.step[11:] = amp

        self.Kc = self.m.FV(value=0.01, lb=Kc_min, ub=Kc_max)
        self.Kc.STATUS = 1

        # tauI=3.0
        self.Ti = self.m.FV(value=100, lb=Ti_min, ub=Ti_max)
        self.Ti.STATUS = 1

        # tauD=0.0
        self.Td = self.m.FV(value=100, lb=Td_min, ub=Td_max)
        self.Td.STATUS = 1

        self.OP_0 = 0.0
        self.OP = self.m.Var(value=0, lb=outmin, ub=outmax)
        self.PV = self.m.Var(value=0)
        self.SP = self.m.Param(value=self.step)
        self.Intgl = self.m.Var(value=0)
        self.err = self.m.Intermediate(self.SP - self.PV)
        self.overshoot=self.m.if2(self.err+0.02*self.SP,-self.err,0)
        self.risetime=self.m.if2(self.err-0.1*self.SP,0,self.err)
        self.settlingtime=self.m.if2(self.err-0.2*self.SP,-self.err,0)
        self.settlingtime=self.settlingtime-self.overshoot

        self.m.Equation(self.Intgl.dt() == self.err)
        self.m.Equation(self.OP == self.OP_0 + self.Kc * self.err + (self.Kc / self.Ti) * self.Intgl
                        - self.Kc * self.Td * self.PV.dt())
        self.m.Obj(self.err ** 2 + overshootweight*self.overshoot**2+risetimeweight*self.risetime**2+settlingtimeweight*self.settlingtime**2)
        # TODO make UI control for overshoot weight

        # Process model
        # convert transfer function to statespace
        A, B, C, D = tf2ss(tf_num, tf_den)
        # Find order of equation
        order = len(A)
        x = self.m.Array(self.m.Var, (order))
        # create state variables
        eqn = np.dot(A, x)
        eqn2 = np.dot(C, x)

        for i in range(order):
            self.m.Equation(x[i].dt() == eqn[i] + B[i][0] * self.OP)

        self.m.Equation(self.PV == eqn2[0] + D[0][0] * self.OP)

        self.m.options.IMODE = 6
        self.m.options.MAX_ITER=1000
        # self.m.options.OTOL=0.5
        PIDvals = collections.namedtuple('PIDvals', ['Kc', 'Ti', 'Td'])
        StepResponse=collections.namedtuple('StepResponse',['time','step','PV','OP'])
        print(self.overshoot.value)

        try:
            self.m.solve()

            return PIDvals(self.Kc.value[0],self.Ti.value[0],self.Td.value[0]),StepResponse(self.m.time, self.step,self.PV.value,self.OP.value)

        except Exception:
            print("no solution found")
            return 0

class PIDAutotuneRT:
    def __init__(self, Y0,a,a_fine,method=MethodList.TL_PI,cycles=5,midpoint=0):
        """
        Autotuner based on relay feedback method
        Parameters
        ----------
                Y0 : float
                    Setpoint
                a : float
                    Amplitude of control signal
        """

        self.OP=np.array([])
        self.PV=np.array([])
        self.Err=np.array([])
        self.sampling=0
        self.currentTime=0
        self.ready=False
        self.currentOutput=a
        self.cycles=cycles
        self.zerocrosses=0
        self.zerocrossingindices=np.array([])
        self.setpoint=Y0
        self.OPamp=a
        self.OPlow=midpoint-self.OPamp/2
        self.OPfine=a_fine
        self.method=method
        self.status=TuningStatus.COARSE_RELAY
        self.captureTime=0
        self.postTime=0

        #start scheduler thread



    def nextVal(self,currentPV,currentOP):
        if self.currentTime==0:
            self.currentTime=time.time()
        else:
            self.sampling=time.time()-self.currentTime
            self.currentTime=time.time()
            if self.status==TuningStatus.COARSE_RELAY or self.status==TuningStatus.FINE_RELAY:
                self.PV=np.append(self.PV,currentPV)
                self.Err=np.append(self.Err,self.setpoint-currentPV)
                zerocrossings=self._zeroCrossings()
                print(zerocrossings)
                if zerocrossings>self.zerocrosses:
                    self._toggleOutput()
                    self.zerocrosses+=1
                    if self.zerocrosses > 2 * self.cycles:
                        self.status = TuningStatus.COARSE_READY if self.status==TuningStatus.COARSE_RELAY else TuningStatus.FINE_READY
                self.OP=np.append(self.OP,self.currentOutput)

            elif self.status==TuningStatus.COARSE_READY:
                self.status=TuningStatus.COARSE_SETTLING
                #reset PV and Err arrays
                self.PV=np.array([])
                self.Err=np.array([])
                self.OP=np.array([])
                self.zerocrossingindices = np.array([])
                self.zerocrosses = 0
                self.captureTime=time.time()

            elif self.status==TuningStatus.DWELL:
                if time.time()-self.postTime>ATSETTLINGTIME and self.postTime!=0:
                    self.currentOutput = self.OPlow + self.OPamp
                    self.status=TuningStatus.FINE_RELAY


            elif self.status==TuningStatus.COARSE_SETTLING:
                Err=self.setpoint-currentPV
                delta=time.time()-self.captureTime
                if (Err<0.01*self.setpoint and Err>-0.01*self.setpoint):
                    pass
                else:
                    self.captureTime=time.time()

                if delta>ATSETTLINGTIME:
                    self.OPlow=currentOP-self.OPfine/2
                    self.OPamp=self.OPfine
                    self.currentOutput=self.OPlow
                    self.postTime=time.time()
                    self.status=TuningStatus.DWELL



                print(delta)






        return self.currentOutput,self.status

    def outputReady(self):
        return self.ready

    def PIDparameters(self):
        if self.status==TuningStatus.COARSE_READY or self.status==TuningStatus.FINE_READY:
            b,Tu=self._calculateInputs()
            print(b)
            print(Tu)
            Ku = (4 / math.pi) * (self.OPamp / b)
            Td=0
            Ti=9999
            Kc=0
            Kc=METHODFACTORS[self.method][0]*Ku
            Ti=METHODFACTORS[self.method][1]*Tu
            Td=METHODFACTORS[self.method][2]*Tu
            # if self.method==0:
            #     Kc=Ku/2
            # elif self.method==1:
            #     Kc=Ku/2.2
            #     Ti=Tu/1.2
            # elif self.method==2:
            #     Kc=Ku/1.7
            #     Ti=Tu/2
            #     Td=Tu/8
            # elif self.method==3:
            #     Kc=Ku/3.2
            #     Ti=2.2*Tu
            # elif self.method==4:
            #     Kc=Ku/2.2
            #     Ti=2.2*Tu
            #     Td=Tu/6.3

            return {'Kc': Kc, 'Ti':Ti,'Td':Td}
        else:
            return {'Kc':0,'Ti':9999,'Td':0}

    @classmethod
    def convertPID(cls,Kp,Ti,Td,initialMethod:MethodList.ZN_PI,finalMethod:MethodList.TL_PI):
        Kpn=Kp*METHODFACTORS[finalMethod][0]/(METHODFACTORS[initialMethod][0])
        if (METHODFACTORS[initialMethod][1]) !=0:
            Tin = Ti * METHODFACTORS[finalMethod][1] / (METHODFACTORS[initialMethod][1])
        else:
            Tin=0
        if (METHODFACTORS[initialMethod][2]) !=0:
            Tdn = Td * METHODFACTORS[finalMethod][2] / (METHODFACTORS[initialMethod][2])
        else:
            Tdn=0

        return {'Kp':Kpn,'Ti':Tin,'Td':Tdn}

    def _toggleOutput(self):
        if self.currentOutput==self.OPlow:
            self.currentOutput=self.OPamp+self.OPlow
        else:
            self.currentOutput=self.OPlow


    def _zeroCrossings(self):
        if np.any(self.Err):
            Err_nosmall=self.Err[(self.Err>ZEROCROSSINGTOL*self.setpoint)|(self.Err<-ZEROCROSSINGTOL*self.setpoint)]
            self.zerocrossingindices=np.where(np.diff(np.sign(Err_nosmall)))[0]
            return len(self.zerocrossingindices)
        else:
            return 0

    def _calculateInputs(self):
        #remove all elements before first zero crossing index:
        for i in range(self.zerocrossingindices[0]):
            self.PV=np.delete(self.PV, 0)
        b=np.max(self.PV)-np.min(self.PV)
        diff=np.array([])
        for i in range(len(self.zerocrossingindices)-1):
            diff=np.append(diff,self.zerocrossingindices[i+1]-self.zerocrossingindices[i])

        # diff=PIDAutotuneRT.reject_outliers(diff)
        Tu=2*np.mean(diff)*self.sampling

        return b,Tu

    @classmethod
    def reject_outliers(cls,data, m=2.):
        d = np.abs(data - np.median(data))
        mdev = np.median(d)
        s = d / mdev if mdev else 0.
        return data[s < m]






if __name__=="__main__":
    # pid=PID(1,1,1,0,10)
    # t=np.linspace(0,10,100)
    # print(pid.apply(1,0.5))

    # Autotune=PIDAutotune()



    # for i in range(len(t)):
    #     next(pid.apply())
    pid,res=PID.autotune_offline([1], [1, 10], 30, 100, 1)
    print(pid)
    print(res)