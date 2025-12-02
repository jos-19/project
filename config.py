"""
config.py
=========
Central configuration for pins, network, and audio tuning.
"""

# --- NETWORK CREDENTIALS (CHANGE THESE) ---
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# --- Hardware Pins ---
I2C_SCL_PIN = 22
I2C_SDA_PIN = 21
BUTTON_PIN  = 14
MIC_PIN     = 34

# --- Display Settings ---
OLED_WIDTH  = 128
OLED_HEIGHT = 64

# --- Audio Tuning ---
IGNORE_LOW_BINS = 2     # Ignore DC offset/low rumble
NOISE_GATE      = 400   # Threshold to silence static
GAIN            = 3.0   # Visual multiplier
SPEECH_BARS     = 20    # Number of bars in Speech Mode
SAMPLE_LENGTH   = 256   # FFT Sample Size
FIXED_MAX_MAG   = 3000  # For web graph scaling
