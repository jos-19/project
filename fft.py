import math

# --- CACHE: Pre-calculated values to speed up loops ---
_window_cache = {}

def get_magnitude(data):
    """
    Calculates FFT magnitudes.
    Non-recursive and uses caching for speed.
    """
    n = len(data)
    if n == 0: return []

    # 1. OPTIMIZATION: Only calculate the Hanning window ONCE.
    if n not in _window_cache:
        # Pre-calculate window to avoid math.cos calls every frame
        _window_cache[n] = [0.5 * (1 - math.cos(2 * math.pi * i / (n - 1))) for i in range(n)]
    
    window = _window_cache[n]
    
    # 2. Remove DC Offset (Center signal at 0)
    avg = sum(data) / n
    
    # 3. Apply Window & Prepare Complex List
    # We create the complex list manually to avoid overhead
    # (val - avg) removes DC offset
    # * w applies the Hanning window
    complex_data = [complex((x - avg) * w, 0) for x, w in zip(data, window)]
    
    # 4. Run Iterative FFT
    fft_in_place(complex_data)
    
    # 5. Calculate Magnitude
    # We only return the first half (positive frequencies)
    # Using abs(c) is faster than math.sqrt(r**2 + i**2) in MicroPython
    half_n = n // 2
    return [abs(x) for x in complex_data[:half_n]]

def fft_in_place(x):
    """
    A non-recursive, in-place implementation of the Cooley-Tukey FFT.
    Significantly faster than recursive versions on ESP32.
    """
    n = len(x)
    
    # --- Bit-reversal Permutation ---
    # Swaps data indices to prepare for the butterfly loops
    j = 0
    for i in range(n):
        if i < j:
            x[i], x[j] = x[j], x[i]
        m = n >> 1
        while j >= m and m > 0:
            j -= m
            m >>= 1
        j += m
        
    # --- Butterfly Operations ---
    # Processes the FFT in stages (loops) rather than recursion
    mmax = 1
    pi_val = math.pi # Local var access is faster
    
    while n > mmax:
        istep = mmax << 1
        theta = -pi_val / mmax
        
        # Pre-calculate twist factors
        w_twist_real = math.cos(theta)
        w_twist_imag = math.sin(theta)
        
        w_real = 1.0
        w_imag = 0.0
        
        for m in range(mmax):
            # Process this "wing" of the butterfly across the array
            for i in range(m, n, istep):
                j = i + mmax
                
                # Complex multiplication logic expanded for speed
                # (a + bi)(c + di) = (ac - bd) + (ad + bc)i
                xr = x[j].real
                xi = x[j].imag
                
                temp_real = w_real * xr - w_imag * xi
                temp_imag = w_real * xi + w_imag * xr
                
                # Update values in-place
                xi_real = x[i].real
                xi_imag = x[i].imag
                
                x[j] = complex(xi_real - temp_real, xi_imag - temp_imag)
                x[i] = complex(xi_real + temp_real, xi_imag + temp_imag)
            
            # Update rotation factors
            t = w_real
            w_real = t * w_twist_real - w_imag * w_twist_imag
            w_imag = t * w_twist_imag + w_imag * w_twist_real
            
        mmax = istep
