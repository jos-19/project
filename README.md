## Audio spectrum analyzer
<img width="1013" height="729" alt="image" src="https://github.com/user-attachments/assets/7aed0384-058c-43fa-85e8-4d534d7af0b3" />


The main objective of the project is to listen to the surrounding audio and display the spectrum of that.

## Features
* Spectrum on the OLED display
* Min/Max dB values
* On-device control with push buttons
* App control
* The app also works as the display

## Hardware components
* Screen: SH1106
* Microfone: LM393
* Microcontroller: ESP32



# import scipy.fft info:https://docs.scipy.org/doc/scipy/tutorial/fft.html#fast-fourier-transforms
# Audio compression using DCT https://mate.dm.uba.ar/~asalort/varios/dct1d/dct1d.html
# Applications https://www.tecnare.com/es/article/analisis-de-fourier-aplicado-al-audio-dominio-tiempo-frecuencia/
# Info https://es.python-3.com/?p=266
# FIR https://www.tecnare.com/es/article/la-importancia-de-los-filtros-fir/
# https://pysdr.org/es/content-es/filters.html
