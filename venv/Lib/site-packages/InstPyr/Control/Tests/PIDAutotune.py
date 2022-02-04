from gekko import GEKKO
import numpy as np
import matplotlib.pyplot as plt





m=GEKKO()

tf=80 #seconds
m.time=np.linspace(0,tf,2*tf+1)
# print(m.time)
step=np.zeros(2*tf+1)
step[3:40]=2.0
step[40:]=5.0

#PID controller model
Kc=m.FV(value=5.0,lb=1.0,ub=1000.0)
Kc.STATUS=1

# tauI=3.0
tauI=m.FV(value=2.0, lb=0.1, ub=100)
tauI.STATUS=1


# tauD=0.0
tauD=m.FV(value=1, lb=0.01, ub=100)
tauD.STATUS=1


OP_0=0.0
OP=m.Var(value=0, lb=0, ub=70)
PV=m.Var(value=0)
SP=m.Param(value=step)
Intgl=m.Var(value=0)
err=m.Intermediate(SP-PV)
m.Equation(Intgl.dt()==err)
m.Equation(OP==OP_0+Kc*err+(Kc/tauI)*Intgl-Kc*tauD*PV.dt())
m.Obj(err**2-0.01*err)

#Process model
Kp=1
tauP=1
x=m.Var(value=0)
m.Equation(tauP*x.dt()+2*x==OP)
m.Equation(tauP*PV.dt()+4*PV==Kp*x)

# m.options.IMODE=4
m.options.IMODE=6
m.solve()
print('Kc: '+str(Kc.value[0]))
print('TauI: '+str(tauI.value[0]))
print('TauD: '+str(tauD.value[0]))

plt.figure()
plt.subplot(2,1,1)
plt.plot(m.time,OP.value)
plt.subplot(2,1,2)
plt.plot(m.time, SP.value)
plt.plot(m.time,PV.value)
plt.show()

