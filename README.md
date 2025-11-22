## Audio spectrum analyzer

<img width="1066" height="755" alt="Screenshot 2025-11-20 151451" src="https://github.com/user-attachments/assets/37a1bcab-d63e-458c-b9a5-55f53e84ecd9" />

The main objective of the project is to listen to the surrounding audio and display the spectrum of that.

Audio Spectrum Analyzer
1. Problem Statement & Solution Overview
The Problem
Audio analysis is crucial for various applications, from sound engineering to environmental noise monitoring. However, visualized audio data is often inaccessible without expensive, bulky equipment or complex desktop software. There is a need for a portable, low-cost solution that can visualize sound frequencies in real-time to identify dominant frequencies, noise levels, and spectral balance in an immediate environment.

The Solution
We are designing a portable Audio Spectrum Analyzer based on the ESP32 microcontroller. This system will capture environmental audio, process it using Fast Fourier Transform (FFT) algorithms, and visualize the frequency spectrum on a compact OLED display. Additionally, the system features wireless connectivity (Bluetooth/Wi-Fi) to mirror the display on a mobile app and allow for remote control, making it a versatile tool for educational and hobbyist audio analysis.

## Features
* Spectrum on the OLED display
* Min/Max dB values
* On-device control with push buttons
* App control
* The app also works as the display

## Hardware components
* Screen: SH1106
* Microfone: MAX4466
* Microcontroller: ESP32



# import scipy.fft info:https://docs.scipy.org/doc/scipy/tutorial/fft.html#fast-fourier-transforms
# Audio compression using DCT https://mate.dm.uba.ar/~asalort/varios/dct1d/dct1d.html
# Applications https://www.tecnare.com/es/article/analisis-de-fourier-aplicado-al-audio-dominio-tiempo-frecuencia/
# Info https://es.python-3.com/?p=266
# FIR https://www.tecnare.com/es/article/la-importancia-de-los-filtros-fir/
# https://pysdr.org/es/content-es/filters.html
