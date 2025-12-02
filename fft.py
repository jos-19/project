import math
import cmath

# --- OPTIMIZATION 1: Window Caching ---
# We store the Hanning window here so we calculate it ONLY ONCE,
# not every single frame.
_window_cache = {}

def get_magnitude(data):
    """
    Takes audio samples and returns frequency magnitudes.
    Optimized for ESP32 (Iterative processing & Caching).
    """
    n = len(data)
    if n == 0: return []

    # 1. Prepare Window (Lazy Load)
    if n not in _window_cache:
        # Pre-calculate the window values only once
        _window_cache[n] = [0.5 * (1 - math.cos(2 * math.pi * i / (n - 1))) for i in range(n)]
    
    window = _window_cache[n]
    
    # 2. Remove DC Offset & Apply Window
    # Doing this in a single pass is faster than multiple list loops
    avg = sum(data) / n
    
    # Create complex numbers directly for the FFT
    # (val - avg) removes DC offset
    # * w applies the window
    complex_data = [complex((x - avg) * w, 0) for x, w in zip(data, window)]
    
    # 3. FFT (Iterative - Much Faster)
    fft_in_place(complex_data)
    
    # 4. Magnitude Calculation
    # abs(c) in MicroPython uses C-level optimization for sqrt(r^2 + i^2)
    # We only return the first half (positive frequencies)
    half_n = n // 2
    return [abs(x) for x in complex_data[:half_n]]

def fft_in_place(x):
    """
    A non-recursive, in-place implementation of the Cooley-Tukey FFT.
    This avoids the heavy memory allocation of the recursive version.
    """
    n = len(x)
    
    # --- Bit-reversal permutation ---
    # Swaps data into the correct order before processing
    j = 0
    for i in range(n):
        if i < j:
            x[i], x[j] = x[j], x[i]
        m = n >> 1
        while j >= m and m > 0:
            j -= m
            m >>= 1
        j += m
        
    # --- Butterfly operations ---
    # Iterative approach (Loops instead of Recursion)
    mmax = 1
    while n > mmax:
        istep = mmax << 1
        theta = -math.pi / mmax
        
        # Pre-calculate twist factors
        w_twist_real = math.cos(theta)
        w_twist_imag = math.sin(theta)
        
        w_real = 1.0
        w_imag = 0.0
        
        for m in range(mmax):
            for i in range(m, n, istep):
                j = i + mmax
                
                # Complex multiplication: temp = w * x[j]
                # (a + bi)(c + di) = (ac - bd) + (ad + bc)i
                xr = x[j].real
                xi = x[j].imag
                
                temp_real = w_real * xr - w_imag * xi
                temp_imag = w_real * xi + w_imag * xr
                
                # Butterfly calculation
                # x[j] = x[i] - temp
                # x[i] = x[i] + temp
                xi_real = x[i].real
                xi_imag = x[i].imag
                
                x[j] = complex(xi_real - temp_real, xi_imag - temp_imag)
                x[i] = complex(xi_real + temp_real, xi_imag + temp_imag)
            
            # Update w for next iteration
            t = w_real
            w_real = t * w_twist_real - w_imag * w_twist_imag
            w_imag = t * w_twist_imag + w_imag * w_twist_real
            
        mmax = istep
