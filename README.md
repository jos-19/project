Poster SIZE A3 at least

## Audio spectrum analyzer

<img width="1193" height="869" alt="Story Mind Map Brainstorm Whiteboard in Blue Orange Minimal Style" src="https://github.com/user-attachments/assets/24287983-2199-4979-a8f8-3cd1661b3ee9" />

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

### Block Diagram

<img width="963" height="789" alt="icrophone (MAX4466)" src="https://github.com/user-attachments/assets/7bf1a5eb-3fe4-4ab9-9995-54a794bcaf6c" />

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

# 5. Phase 2

## Project Demo

![PXL_20251127_145709558](https://github.com/user-attachments/assets/2d00860d-604d-4f28-92fd-ef1b7873f49a)

youtube link here

## Documentation
**(https://jos-19.github.io/project/)**

### File Structure
```text
├── main.py              # Entry point: orchestrates Audio, Display, and Network
├── config.py            # Central configuration (Pins, WiFi, Audio Tuning)
├── audio_processor.py   # Handles ADC sampling and dB calculations
├── fft.py               # Custom pure-Python FFT implementation
├── display_manager.py   # Manages OLED drawing and I2C communication
├── network_manager.py   # Asynchronous Web Server & HTML content
└── docs/                # Sphinx documentation source files
``` 

## Circuit schematic
  
<img width="1497" height="920" alt="Schematic_New-Project_2025-11-30-1" src="https://github.com/user-attachments/assets/1799aa26-7ab0-4a73-8bd4-fab9bf662a34" />


## 6. References & Resources

### 1. Web Interface & Networking (WiFi & Dashboard)
Resources used to build the asynchronous web server and the real-time browser graph.
* **MicroPython Network & Sockets:** Used `network` for WiFi connection and `usocket` for creating the non-blocking HTTP server.
    * [MicroPython Network Docs](https://docs.micropython.org/en/latest/library/network.html)
    * [MicroPython Socket Docs](https://docs.micropython.org/en/latest/library/usocket.html)
* **HTML5 Canvas API:** The "Spectrum" graph on the webpage is drawn using the HTML5 `<canvas>` element and JavaScript.
    * [MDN Canvas API Tutorial](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial)
* **JavaScript Fetch API:** The webpage uses `fetch()` to request JSON data from the ESP32 without reloading the page (AJAX).
    * [MDN Fetch API Documentation](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
* **CSS Flexbox:** Used for the responsive layout of the dashboard cards.
    * [CSS Flexbox Guide](https://css-tricks.com/snippets/css/a-guide-to-flexbox/)

### 2. Software Libraries & Drivers
External drivers and core libraries used for hardware control.
* **MicroPython Standard Library:** Core hardware control (`machine` for I2C/ADC).
    * [MicroPython Documentation](https://docs.micropython.org/en/latest/library/index.html)
* **SH1106 OLED Driver:** Custom driver for the 1.3" OLED display using I2C.
    * [SH1106 Source Repository](https://github.com/robert-hh/SH1106)
* **`cmath` (Complex Math):** Python standard library used for complex number exponentials required by the recursive FFT algorithm.
    * [Python cmath Documentation](https://docs.python.org/3/library/cmath.html)

### 3. Key Algorithms & Signal Processing
Custom algorithms implemented for DSP and signal analysis.
* **FFT Implementation (Cooley-Tukey):** Recursive implementation of the Cooley-Tukey algorithm for the ESP32.
    * *Reference:* [SciPy FFT Tutorial](https://docs.scipy.org/doc/scipy/tutorial/fft.html#fast-fourier-transforms)
    * *Algorithm Guide:* [Fast Fourier Transform Information](https://es.python-3.com/?p=266)
* **Windowing Functions:** A Hanning Window is applied to audio samples to reduce spectral leakage.
    * *Concept:* [Audio Analysis - Time/Frequency Domain](https://www.tecnare.com/es/article/analisis-de-fourier-aplicado-al-audio-dominio-tiempo-frecuencia/)
* **Digital Filtering:** Concepts of Finite Impulse Response (FIR) were reviewed for signal conditioning.
    * *Reference:* [FIR Filters Guide](https://pysdr.org/es/content-es/filters.html)
    * *Additional Reading:* [Importance of FIR Filters](https://www.tecnare.com/es/article/la-importancia-de-los-filtros-fir/)

### 4. Audio Theory & Applications
Background research used to design the metering logic.
* **Audio Compression:** Investigated Discrete Cosine Transform (DCT).
    * *Source:* [Audio compression using DCT](https://mate.dm.uba.ar/~asalort/varios/dct1d/dct1d.html)
* **Decibel Calculation:** Implemented Root Mean Square (RMS) calculations to derive accurate dB levels.
