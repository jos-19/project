import machine
import math
import time
import fft  # Your existing pure python library
import config

class AudioProcessor:
    """
    Handles analog input reading, FFT processing, and dB calculations.
    """

    def __init__(self):
        # Initialize ADC
        self.adc = machine.ADC(machine.Pin(config.MIC_PIN))
        self.adc.width(machine.ADC.WIDTH_12BIT)
        self.adc.atten(machine.ADC.ATTN_11DB)
        
        # Calibrate Sampling Rate
        self.real_sampling_rate = self._measure_sampling_rate()
        self.hz_per_bin = self.real_sampling_rate / config.SAMPLE_LENGTH
        self.max_freq = self.real_sampling_rate / 2
        
        print(f"Audio Init: {self.real_sampling_rate}Hz | Res: {self.hz_per_bin:.1f}Hz")

    def read_audio(self):
        """Reads raw samples from ADC (Optimized)."""
        read_func = self.adc.read
        return [read_func() for _ in range(config.SAMPLE_LENGTH)]

    def get_magnitudes(self, raw_data):
        """Calculates FFT magnitudes."""
        return fft.get_magnitude(raw_data)

    def calculate_db(self, raw_data):
        """Calculates RMS Decibels."""
        if not raw_data: return 0
        avg = sum(raw_data) / len(raw_data)
        centered = [x - avg for x in raw_data]
        squared_sum = sum(x*x for x in centered)
        mean_square = squared_sum / len(centered)
        rms = math.sqrt(mean_square)

        if rms > 1:
            db = 20 * math.log10(rms / 2000.0) + 100 
            return max(0, db)
        return 0.0

    # --- NEW FUNCTION FOR BAND MONITOR MODE ---
    def analyze_bands(self, magnitudes):
        """Finds the most and least active frequency bands."""
        if not magnitudes: return (0, 0, 0, 0)

        # Ignore low bins (DC offset/rumble)
        start_index = config.IGNORE_LOW_BINS
        
        # Filter magnitudes and get indices relative to the start_index
        active_mags = magnitudes[start_index:]
        
        if not active_mags: return (0, 0, 0, 0)
        
        # Find Max/Min magnitude values and their indices
        max_mag = 0
        max_idx_relative = 0
        min_mag = 999999
        min_idx_relative = 0
        
        for i, mag in enumerate(active_mags):
            if mag > max_mag:
                max_mag = mag
                max_idx_relative = i
            
            # Only consider "quiet" bins if they are above the noise floor (or zero)
            if mag < min_mag and mag > 0:
                min_mag = mag
                min_idx_relative = i

        # Convert index back to frequency (Hz)
        hz_per_bin = self.hz_per_bin
        max_freq = int((max_idx_relative + start_index) * hz_per_bin)
        min_freq = int((min_idx_relative + start_index) * hz_per_bin)

        # Return (max_freq, max_magnitude, min_freq, min_magnitude)
        return (max_freq, max_mag, min_freq, min_mag)

    def calculate_display_bars(self, magnitudes, min_hz, max_hz, num_bars):
        """Bins FFT data into bars for the display."""
        start_idx = int(min_hz / self.hz_per_bin)
        end_idx  = int(max_hz / self.hz_per_bin)
        
        if start_idx < config.IGNORE_LOW_BINS: start_idx = config.IGNORE_LOW_BINS
        if end_idx >= len(magnitudes): end_idx = len(magnitudes)
        if end_idx <= start_idx: return [0] * num_bars
        
        num_fft_bins_in_range = end_idx - start_idx
        bins_per_bar = num_fft_bins_in_range / num_bars 
        
        display_bars = []
        for i in range(num_bars):
            bin_start = start_idx + int(i * bins_per_bar)
            bin_end = start_idx + int((i + 1) * bins_per_bar)
            
            if bin_end == bin_start: bin_end = bin_start + 1
            if bin_end > len(magnitudes): bin_end = len(magnitudes)

            bar_magnitudes = magnitudes[bin_start:bin_end]
            
            mag = 0
            if bar_magnitudes: mag = max(bar_magnitudes)
            if mag < config.NOISE_GATE: mag = 0
            display_bars.append(mag)
            
        return display_bars

    def _measure_sampling_rate(self):
        """Internal calibration."""
        self.read_audio()
        start = time.ticks_us()
        self.read_audio()
        end = time.ticks_us()
        diff = time.ticks_diff(end, start)
        return int(1000000 / (diff / config.SAMPLE_LENGTH))
