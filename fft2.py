try:
    from ulab import numpy as np
except ImportError:
    print("Error: `ulab` library not found!")
    print("Please verify your MicroPython firmware includes ulab.")
    raise

def get_magnitude(data):
    """
    Calculates FFT magnitudes using ulab (C-optimized NumPy).
    This is extremely fast compared to pure Python.
    """
    n = len(data)
    
    # 1. Convert raw list to ulab array (float)
    # This moves the data into C-memory for fast processing
    wave = np.array(data, dtype=np.float)
    
    # 2. Remove DC Offset (Vectorized)
    wave = wave - np.mean(wave)
    
    # 3. Apply Hanning Window (Vectorized)
    # Creating the window in ulab is faster than reading a cached Python list
    idx = np.arange(n)
    window = 0.5 * (1 - np.cos(2 * np.pi * idx / (n - 1)))
    wave = wave * window
    
    # 4. FFT
    # ulab.numpy.fft.fft returns a tuple: (real_part, imaginary_part)
    real, imag = np.fft.fft(wave)
    
    # 5. Calculate Magnitude
    # mag = sqrt(real^2 + imag^2)
    # ulab handles this math on the whole array at once (SIMD-like speed)
    mags = np.sqrt(real*real + imag*imag)
    
    # 6. Return Data
    # We only want the first half (positive frequencies)
    # We convert back to a standard Python list because the rest 
    # of your app expects a list, not a ulab array.
    half_n = n // 2
    return list(mags[:half_n])
