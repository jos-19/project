
"""
Created on Sun Nov 23 19:19:15 2025

@author: Jose
"""
import math

def dft(x,Fs):
    """ 
    Given an input vector x, returns an output vector y along 
    with a frequency axis freq
    """
    
    N = len(x)
    half_N=N//2 + 1
    
    y_real=[0.0] * half_N
    y_imag=[0.0] * half_N
    

    freq = [(Fs/N) * i for i in range(half_N)]
    
    for k in range(half_N):
        y_real[k]=0.0
        y_imag[k]=0.0
        factor=2* math.pi*k/N
        
        for n in range(N):
            angle=factor * n
            y_real[k] += x[n] *math.cos(angle)
            y_imag[k] -= x[n] *math.sin(angle)
    
    y=[complex(r,i) for r,i in zip(y_real, y_imag)]
    
    
    return y,freq
