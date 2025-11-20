import math
import cmath # CRITICAL: Needed for complex number math

def fft(x):
    """
    A recursive implementation of the 1D Cooley-Tukey FFT.
    x must be a list of complex numbers (or reals) with length power of 2.
    Returns a list of complex numbers.
    """
    n = len(x)
    if n <= 1:
        return x
    
    even = fft(x[0::2])
    odd =  fft(x[1::2])
    
    # FIXED: Use cmath.exp instead of math.exp
    # The term (-2j * ...) is a complex number. Standard math.exp fails on this.
    T = [cmath.exp(-2j * math.pi * k / n) * odd[k] for k in range(n // 2)]
    
    return [even[k] + T[k] for k in range(n // 2)] + \
           [even[k] - T[k] for k in range(n // 2)]

def get_magnitude(data):
    """
    Helper to take audio samples and return frequency magnitudes.
    """
    # 1. Remove DC offset (center around 0)
    if not data: return []
    avg = sum(data) / len(data)
    data = [x - avg for x in data]
    
    # 2. Apply Hanning Window
    # math.cos is fine here because the inside calculation is all Real numbers (floats)
    N = len(data)
    windowed = [data[i] * (0.5 * (1 - math.cos(2 * math.pi * i / (N - 1)))) for i in range(N)]
    
    # 3. FFT
    complex_spectrum = fft(windowed)
    
    # 4. Calculate magnitude of first half
    # Magnitude = sqrt(Real^2 + Imag^2)
    # math.sqrt is fine here because (real^2 + imag^2) results in a Real number
    half_n = N // 2
    magnitudes = []
    for i in range(half_n):
        c = complex_spectrum[i]
        mag = math.sqrt(c.real**2 + c.imag**2)
        magnitudes.append(mag)
        
    return magnitudes
