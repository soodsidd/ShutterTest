# class SysID:
#     def __init__(self):
#         pass
#
#     @classmethod
#
import numpy as np
from scipy import signal as sig
from scipy import optimize as opt
import pandas as pd
import matplotlib.pyplot as plt
from gekko import GEKKO
import math

MODELPATH='C:\\Users\\soods\\Desktop\\Python\\InstPyr\\src\\InstPyr\\Control\\Models\\Step_response_Full_Red.xls'


class TF_identificator:
    def __init__(self):
        self.tf = None
        self.inputs = None
    @classmethod
    def first_order_mdl(cls,t,input, k, pole):
        tf = sig.TransferFunction(k, [pole, 1])
        to, yo, xo = sig.lsim2(tf, U=input, T=t)
        return yo

    def first_order_mdl_N(self, t, k, pole):
        self.tf = sig.TransferFunction(k, [pole, 1])
        to, yo, xo = sig.lsim2(self.tf, U=self.inputs, T=t)
        return yo

    @classmethod
    def second_order_mdl(cls,t, input,zero, k, wn, delta):
        tf = sig.TransferFunction([k*(wn**2),k*(wn**2)*zero], [1, 2*delta*wn, wn**2])
        to, yo, xo = sig.lsim2(tf, U=input, T=t)
        return yo

    @classmethod
    def second_order_mdl_overdamped(cls, t,input, k,T1,T2,T3):
        tf = sig.TransferFunction([T3*k,k], [T1*T2,(T1+T2),1])
        to, yo, xo = sig.lsim2(tf, U=input, T=t)
        return yo


    def identify_first_order(self, t, u, orig_output, method='lm', p0=[1.0, 1.0]):
        self.inputs = u
        params, params_cov = opt.curve_fit(self.first_order_mdl_N, t, orig_output,
                                           method=method, maxfev=1000, p0=p0)
        print(params_cov)
        simout=TF_identificator.first_order_mdl(t,u,params[0],params[1])
        res=self.calculate_residual(orig_output,simout)

        return {'k': params[0], 'tau': params[1],'sim':simout,'res':res}


    def identify_second_order(self, t, u, orig_output, method='trf', p0=[1.0, 0.1, 1],lb=[0,0,1],ub=[1000,1,100]):
        self.inputs = u
        params, params_cov = opt.curve_fit(self.second_order_mdl, t, orig_output, bounds=(lb,ub),
                                           method=method, maxfev=1000, p0=p0)
        print(params_cov)
        return {'k': params[0], 'wn': params[1], 'zeta': params[2]}

    def identify_first_order_gek(self,time,input,output):
        m = GEKKO()
        m_time = m.Param(value=time)
        m_input = m.Param(value=input)

        m_tau = m.FV(value=1)
        m_tau.STATUS = 1

        m_k = m.FV(value=1)
        m_k.STATUS = 1

        m_output = m.CV(value=output)
        m_output.FSTATUS = 1

        m.Equation(m_output == m_k * (1 - m.exp(-m_time / m_tau)) * m_input)

        m.options.IMODE = 2
        m.options.MAX_ITER=1000

        m.solve()

        simout=TF_identificator.first_order_mdl(time,input,m_k.value[0],m_tau.value[0])

        res=self.calculate_residual(output,simout)

        return {'k':m_k.value[0],
                'tau':m_tau.value[0],
                'sim':simout,
                'res':res}

    def identify_second_order_undamped_gek(self,time,input,output):
        solved=False
        initwn=0.006
        initk=.46
        initzeta=1.6
        wnbounds=[0,0.01]
        Kbounds=[0,1]
        zetabounds=[1,5]

        while solved==False:
            m = GEKKO()
            # m_time = m.Param(value=time)
            m.time=time
            m_input = m.Param(value=input)

            m_wn = m.FV(value=initwn, lb=wnbounds[0],ub=wnbounds[1])
            m_wn.STATUS = 1

            m_k = m.FV(value=initk,lb=Kbounds[0],ub=Kbounds[1])
            m_k.STATUS = 1

            m_zeta = m.FV(value=initzeta,lb=zetabounds[0],ub=zetabounds[1])
            m_zeta.STATUS = 1

            m_output = m.Param(value=output)
            # m_output.FSTATUS = 1

            m_sim=m.Var(value=0)

            err=m.Intermediate(m_output-m_sim)
            m_x=m.Var(value=0)
            abserr=m.if2(err,-err,err)


            m.Equation(m_x.dt()+(m_wn**2)*m_sim==m_k*m_input)
            m.Equation(m_sim.dt()+2*m_zeta*m_wn*m_sim==m_x)

            m.Minimize(err**2)#+abserr)
            m.options.IMODE = 6
            m.options.MAX_ITER = 10000
            m.options.OTOL=1e-8
            m.options.RTOL=1e-8
            try:
                m.solve(disp=True)
                solved=True
            except Exception:
                initwn=np.random.uniform(wnbounds[0],wnbounds[1])
                initk=np.random.uniform(Kbounds[0],Kbounds[1])
                initzeta=np.random.uniform(zetabounds[0],zetabounds[1])
                print(initk,initwn,initzeta)
                solved=False


        print(m_k.value[0])
        print(m_wn.value[0])
        print(m_zeta.value[0])

        plt.figure()
        plt.plot(time,input)
        plt.plot(time,output)
        plt.plot(time,m_sim.value)
        plt.show()

        # print(m_k.value[0])
        # print(m_tau.value[0])
        return {'k': m_k.value[0],
                'wn': m_wn.value[0],
                'zeta':m_zeta.value[0]}

    def identify_second_order_damped_gek(self, time, input, output):
        solved = False
        initT1 = 0.006
        initk = .46
        initT2 = 1.6
        T1bounds = [100, 1200]
        Kbounds = [1, 1000]
        T2bounds = [100, 1200]

        while solved == False:
            m = GEKKO()
            m_input = m.Param(value=input)
            m_time=m.Param(value=time)

            m_T1 = m.FV(value=initT1, lb=T1bounds[0], ub=T1bounds[1])
            m_T1.STATUS = 1

            m_k = m.FV(value=initk,lb=100)
            m_k.STATUS = 1

            m_T2 = m.FV(value=initT2, lb=T2bounds[0], ub=T2bounds[1])
            m_T2.STATUS = 1


            m_output = m.CV(value=output)
            m_output.FSTATUS=1
            # m_output.FSTATUS = 1


            m.Equation(m_output==(m_k/(m_T1+m_T2))*(1+((m_T1/(m_T2-m_T1))*m.exp(-m_time/m_T2))-((m_T2/(m_T2-m_T1))*m.exp(-m_time/m_T1)))*m_input)
            m.options.IMODE = 2
            m.options.MAX_ITER = 10000
            m.options.OTOL = 1e-8
            m.options.RTOL = 1e-8
            try:
                m.solve(disp=True)
                solved = True
            except Exception:
                initT1 = np.random.uniform(T1bounds[0], T1bounds[1])
                initk = np.random.uniform(Kbounds[0], Kbounds[1])
                initT2 = np.random.uniform(T2bounds[0], T2bounds[1])
                print(initk, initT2, initT1)
                solved = False

            print(m_k.value[0])
            print(m_T1.value[0])
            print(m_T2.value[0])

            plt.figure()
            plt.plot(time, input)
            plt.plot(time, output)
            plt.plot(time, m_output.value)
            plt.show()

        # print(m_k.value[0])
        # print(m_tau.value[0])
        # return {'k': m_k.value[0],
        #         'wn': m_wn.value[0],
        #         'zeta': m_zeta.value[0]}

    def identify_second_order_damped(self, time, input, output,dynamicsratiomax=5):
            #response is:
            #K(T3s+1)/((T1s+1)(T2s+1))
            u=np.average(input)
            #K=Y(inf)
            endsamples=5
            K=(np.average(output[len(output)-endsamples:len(output)-1]))/u
            #make a list of indices
            indexes=np.linspace(0,len(time),1)
            #pick a sample randomly
            #third of sample space
            totallen=len(time)
            dynamicsratio=np.linspace(3,dynamicsratiomax,100)
            bestfit={}
            bestratio=0
            minres=1000000000
            for j in range(len(dynamicsratio)):
                #TODO optimize minimization function
                section=int((len(time)-1)/dynamicsratio[j])
                T1arr=[]
                T2arr=[]
                T3arr=[]
                for i in range(section):
                    index=i#np.random.randint(0,third)
                    # print(index)
                    indexes=np.setdiff1d(indexes,index)
                    ti=time[index]
                    y1=output[index]
                    y2=output[2*index]
                    y3=output[3*index]
                    k1=(y1/K)-1
                    k2=(y2/K)-1
                    k3=(y3/K)-1

                    b=4*k1**3*k3-3*k1**2*k2**2-4*k2**3+k3**2+6*k1*k2*k3
                    a1=(k1*k2+k3-np.sqrt(b))/(2*(k1**2+k2))
                    a2=(k1*k2+k3+np.sqrt(b))/(2*(k1**2+k2))

                    beta=(2*k1**3+3*k1*k2+k3-np.sqrt(b))/(np.sqrt(b))

                    T1=-ti/(np.log(a1))
                    T2=-ti/(np.log(a2))
                    T3=beta*(T1-T2)+T1

                    # print(T1,T2,T3)
                    if not math.isnan(T1) or T1<0:
                        if not math.isnan(T2) or T2<0:
                            if not math.isnan(T3) or T3<0:
                                T1arr+=[T1]
                                T2arr+=[T2]
                                T3arr+=[T3]

                T1=np.average(T1arr)
                T2=np.average(T2arr)
                T3=np.average(T3arr)
                # print(np.average(T1arr),np.average(T2arr),np.average(T3arr),K)
                simout = TF_identificator.second_order_mdl_overdamped(time, input,K,T1,T2,T3)
                res=self.calculate_residual(output,simout)
                print(minres)

                if res<=minres:
                    minres=res
                    bestratio=dynamicsratio[j]
                    bestfit={'k':K,
                            'T1':T1,
                            'T2':T2,
                            'T3':T3,
                            'res':res,
                            'sim':simout,
                            'dyn':bestratio}



            # print(res)
            return bestfit
    @classmethod
    def calculate_residual(cls,output,sim):
        err = [x - y for x, y in zip(output, sim)]
        res = sum(map(lambda i: i * i, err))
        return res

if __name__=='__main__':
    # sysid=TF_identificator()
    sysid=TF_identificator()
    df=pd.read_excel(MODELPATH)
    time=np.array(df['Time'].to_list())
    input=np.array(df['Input'].to_list())
    output=np.array(df['Output'].to_list())
    sysid.inputs=input

    # params=sysid.identify_first_order(time,input,output)
    # params=sysid.identify_second_order_undamped(time,input,output)

    params=sysid.identify_second_order_damped(time,input,output,8)


    #
    # print(params['k'])
    # print(params['wn'])
    # print(params['zeta'])
    # params=sysid.identify_first_order(time,input,output)
    # simout=sysid.first_order_mdl(time,input,params['k'],params['tau'])
    # simout=sysid.second_order_mdl_overdamped(time,input,params['k'],params['T1'],params['T2'],params['T3'])
    # print(simout)
    # # print(params['zeta'])
    # print(params['tau'])



    #
    minres_param=params
    print(minres_param['res'])

    print('Final Transfer Function is: {:.2f}*[{:.2f},1]/[{:.2f},{:.2f},1]'.format(minres_param['k'],minres_param['T3'],
                                                                                   (minres_param['T1']*minres_param['T2']),
                                                                                   (minres_param['T1']+minres_param['T2'])))

    plt.figure()
    plt.plot(time,input)
    plt.plot(time,output/np.max(output))
    plt.plot(time,minres_param['sim']/np.max(minres_param['sim']))
    plt.show()
