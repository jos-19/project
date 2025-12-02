import machine
import math
import time
import fft
import config

class AudioProcessor:
    """
    The core engine for audio signal processing.
    
    This class handles the interface with the ESP32 ADC (Analog-to-Digital Converter),
    performs signal normalization, manages the Fast Fourier Transform (FFT) via the
    helper module, and calculates derived metrics like Decibels (dB).

    Attributes:
        adc (machine.ADC): The configured ADC object on the microphone pin.
        real_sampling_rate (int): The actual sampling rate calculated during initialization (approx 10-20kHz).
        hz_per_bin (float): The frequency resolution of each FFT bin (Sampling Rate / Sample Length).
        max_freq (float): The Nyquist frequency (Sampling Rate / 2).
    """

    def __init__(self):
        """
        Initializes the ADC, configures attenuation for 3.3V logic, and performs
        a calibration step to determine the actual sampling rate of the Python loop.
        """
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
        """
        Reads a full buffer of raw audio samples from the microphone.

        This method blocks execution until `config.SAMPLE_LENGTH` samples are collected.
        
        :return: A list of integers (0-4095) representing raw voltage levels.
        :rtype: list[int]
        """
        read_func = self.adc.read
        return [read_func() for _ in range(config.SAMPLE_LENGTH)]

    def get_magnitudes(self, raw_data):
        """
        Converts time-domain raw audio data into frequency-domain magnitudes.

        This acts as a wrapper for the external `fft` module.

        :param list[int] raw_data: The list of raw ADC values collected by `read_audio`.
        :return: A list of floats representing the magnitude of specific frequency bins.
        :rtype: list[float]
        """
        return fft.get_magnitude(raw_data)

    def calculate_db(self, raw_data):
        """
        Calculates the Root Mean Square (RMS) amplitude and converts it to Decibels (dB).

        The formula used is:
        
        .. math::
            dB = 20 \\cdot \\log_{10}(\\frac{RMS}{Reference}) + Offset

        :param list[int] raw_data: The raw audio samples.
        :return: The calculated loudness in dB (clamped to 0.0 minimum).
        :rtype: float
        """
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

    def calculate_analyzer_stats(self, accumulated_mags, count):
        """
        Computes statistical data for the 'Analyzer' mode over a duration of time.

        It averages the accumulated magnitudes, ignores low-frequency noise (DC offset),
        and finds the frequency bin with the highest energy.

        :param list[float] accumulated_mags: Sum of magnitudes per bin over N frames.
        :param int count: The number of frames accumulated.
        :return: A tuple containing (Max Frequency Hz, Min Frequency Hz, Average Magnitude).
        :rtype: tuple(float, float, float)
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
        """
        Bins high-resolution FFT data into a lower number of bars for display.

        This function maps a wide frequency range (e.g., 0-10kHz) into a small number 
        of screen pixels (e.g., 20 bars or 128 pixels). It groups FFT bins and takes 
        the maximum value within that group.

        :param list[float] magnitudes: The full resolution FFT data.
        :param float min_hz: The starting frequency of the view.
        :param float max_hz: The ending frequency of the view.
        :param int num_bars: The target number of bars to generate.
        :return: A list of bar heights ready for drawing.
        :rtype: list[float]
        """
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
        """
        Internal calibration method.
        
        Measures the time it takes to read one full buffer to calculate the 
        effective sampling rate in Hz. This accounts for MicroPython overhead.
        
        :return: The calculated sampling rate in Hz.
        """
        self.read_audio()
        start = time.ticks_us()
        self.read_audio()
        end = time.ticks_us()
        diff = time.ticks_diff(end, start)
        return int(1000000 / (diff / config.SAMPLE_LENGTH))
