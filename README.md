## Audio spectrum analyzer

<img width="1066" height="755" alt="Screenshot 2025-11-20 151451" src="https://github.com/user-attachments/assets/37a1bcab-d63e-458c-b9a5-55f53e84ecd9" />


## 1. Problem Statement & Solution Overview

### The Problem
Audio analysis is crucial for various applications, from sound engineering to environmental noise monitoring. However, visualized audio data is often inaccessible without expensive, bulky equipment or complex desktop software. There is a need for a portable, low-cost solution that can visualize sound frequencies in real-time to identify dominant frequencies, noise levels, and spectral balance in an immediate environment.

### The Solution
We are designing a portable **Audio Spectrum Analyzer** based on the ESP32 microcontroller. This system will capture environmental audio, process it using Fast Fourier Transform (FFT) algorithms, and visualize the frequency spectrum on a compact OLED display. Additionally, the system features wireless connectivity (Bluetooth/Wi-Fi) to mirror the display on a mobile app and allow for remote control, making it a versatile tool for educational and hobbyist audio analysis.

---

## 2. Hardware Components

Below is the list of components selected for the prototype, including justifications for their selection:

| Component | Model | Function | Justification |
| :--- | :--- | :--- | :--- |
| **MCU** | ESP32 FireBeetle | Main Processing Unit | Dual-core processor capable of handling the heavy math (FFT) required for real-time audio processing. Supports MicroPython and has built-in Wi-Fi/BT. |
| **Microphone** | MAX4466 | Audio Input | An adjustable gain electret microphone amplifier. It provides an analog output suitable for the ESP32's ADC, essential for capturing raw audio waveforms. |
| **Display** | SH1106 (OLED) | Visual Output | A 1.3" OLED display using I2C. It is low power, has high contrast for reading charts, and is well-supported by MicroPython drivers. |
| **Controls** | Push Buttons | User Interface | Simple tactile buttons to switch between display modes (e.g., spectrum view vs. dB stats) or reset min/max values. |
| **Power** | Li-Po Battery (Optional) | Power Source | To ensure the device is fully portable and handheld. |

---

## 3. Software Design

The software will be written entirely in **MicroPython**. The architecture is divided into three main loops: Input, Processing, and Output.

### Key Features
* **Real-time FFT:** Converts time-domain audio signals into frequency-domain data.
* **Dual Display Mode:** Spectrum bars on the OLED and mirrored data via App.
* **Statistical Analysis:** Tracks Min/Max dB values and identifies the most/least occupied frequency bands.
* **Remote Control:** BLE/Wi-Fi commands to change settings.

### Logic Flow (Pseudocode)

```python
# System Initialization
Initialize I2C (Display SH1106)
Initialize ADC (Microphone MAX4466)
Initialize Bluetooth/Wi-Fi
Load FFT Library

def capture_audio():
    # Read analog values from microphone
    # Fill buffer with N samples
    return raw_samples

def process_audio(samples):
    # Apply Windowing function (e.g., Hanning) to reduce leakage
    # Perform FFT (Fast Fourier Transform)
    # Calculate magnitude for each frequency bin
    # Identify dominant frequency (Most occupied band)
    # Track Min/Max dB levels
    return spectrum_data, stats

def update_display(spectrum_data, stats):
    # Clear screen
    # Draw frequency bars based on magnitude
    # Draw text for Min/Max dB
    # Push to SH1106 buffer

def main_loop():
    while True:
        # 1. Input
        samples = capture_audio()
        
        # 2. Processing
        spectrum, statistics = process_audio(samples)
        
        # 3. Output
        update_display(spectrum, statistics)
        
        # 4. Connectivity Check
        if app_connected:
            send_data_over_bluetooth(spectrum)
        
        # 5. User Input Check
        if button_pressed:
            change_visualization_mode()
```
# 4. Libraries & Modules
* machine: For ADC, I2C, and Pin control.

* ulab (or custom FFT implementation): For efficient numerical processing and Fourier Transforms.

* sh1106: Driver for the OLED display.

* bluetooth: For communicating with the mobile app.

# 5. References & Resources

* FFT Info: SciPy FFT Tutorial https://docs.scipy.org/doc/scipy/tutorial/fft.html#fast-fourier-transforms
* Audio Theory: Audio Analysis - Time/Frequency Domain https://www.tecnare.com/es/article/analisis-de-fourier-aplicado-al-audio-dominio-tiempo-frecuencia/
* Filtering: FIR Filters Guide https://pysdr.org/es/content-es/filters.html
* Audio compression using DCT https://mate.dm.uba.ar/~asalort/varios/dct1d/dct1d.html
* Applications https://www.tecnare.com/es/article/analisis-de-fourier-aplicado-al-audio-dominio-tiempo-frecuencia/
* Info https://es.python-3.com/?p=266
* FIR https://www.tecnare.com/es/article/la-importancia-de-los-filtros-fir/
