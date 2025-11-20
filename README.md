## Audio spectrum analyzer

<img width="1066" height="755" alt="Screenshot 2025-11-20 151451" src="https://github.com/user-attachments/assets/37a1bcab-d63e-458c-b9a5-55f53e84ecd9" />

The main objective of the project is to listen to the surrounding audio and display the spectrum of that.

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
