import machine
import math
import time
import fft
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
        """Reads raw samples from ADC."""
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

    # --- RESTORED LOGIC FROM OLD CODE ---
    def calculate_analyzer_stats(self, accumulated_mags, count):
        """
        Takes the accumulated magnitudes and the count of frames.
        Returns (max_hz, min_hz, overall_avg)
        """
        if count == 0: return (0, 0, 0)
        
        # Calculate Average per bin
        avgs = [x / count for x in accumulated_mags]
        
        # Slice to ignore DC/Low noise
        valid_data = avgs[config.IGNORE_LOW_BINS:]
        
        if not valid_data: return (0, 0, 0)
        
        # Find Max
        max_val = max(valid_data)
        max_idx = valid_data.index(max_val) + config.IGNORE_LOW_BINS
        max_hz = max_idx * self.hz_per_bin
        
        # Find Min
        min_val = min(valid_data)
        min_idx = valid_data.index(min_val) + config.IGNORE_LOW_BINS
        min_hz = min_idx * self.hz_per_bin
        
        # Overall Average
        overall_avg = sum(valid_data) / len(valid_data)
        
        return (max_hz, min_hz, overall_avg)

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
