import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

n=2
k=np.arange(-n,n+1,1)
N=len(k)
b = 1.0/5*np.array(np.sinc(k/5))
b = 1.0/5*np.array(np.sinc(k/5))*signal.windows.hamming(N)
# b = np.array([1,1,1,1,1])
# b=signal.firwin2(5,[0,1/5,1/5,1],[1,1,0,0])
a = 1

plt.figure()
plt.stem(b)
plt.draw()


w,H = signal.freqz(b,a,512, fs=1)


plt.figure()
plt.plot(w,np.abs(H))
plt.xlabel('Freq')
plt.draw()

plt.figure()
plt.plot(w,np.angle(H))
plt.xlabel('Freq')
plt.show()