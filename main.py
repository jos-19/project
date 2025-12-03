"""
Main Controller Module
======================

This is the entry point of the ESP32 Spectrum Analyzer firmware. 
It coordinates the audio processing, display rendering, and network communications 
in a central infinite loop.

Key Responsibilities:
---------------------
* **State Management:** Holds global state for visualization modes and data accumulation.
* **Input Handling:** Monitors the physical button for mode switching (short press) and output toggling (long press).
* **Loop Execution:** Orchestrates the timing between reading audio, calculating FFTs, and updating the UI.

Global Variables:
-----------------
* ``vis_mode`` (int): 0=Speech, 1=Wide, 2=Analyzer, 3=dB Meter.
* ``output_mode`` (int): 0=OLED Priority (fast framerate), 1=Web Priority (network enabled).

Usage:
------
Flash this file as ``main.py`` to the microcontroller. It will execute automatically on boot.
"""

import machine
import time
import config
from audio_processor import AudioProcessor
from display_manager import DisplayManager
from network_manager import NetworkManager

# --- Global State ---
# vis_mode: 0=Speech, 1=Wide, 2=Analyzer, 3=dB Meter
vis_mode = 0 
VIS_MODE_NAMES = ["Speech", "Wide", "Analyzer", "dB Meter"]

# output_mode: 0=OLED Priority , 1=Web Priority 
output_mode = 0 

# Data containers for Web JSON
latest_mags = []
latest_db_val = 0.0
db_min = 999
db_max = -999

# --- ANALYZER STATE  ---
ANALYZER_DURATION_MS = 5000 
analyzer_accum = []
analyzer_count = 0
analyzer_start_time = 0
analyzer_is_collecting = False
analyzer_results = (0, 0, 0) # (max_hz, min_hz, avg)

def main():
    global vis_mode, output_mode, latest_mags, latest_db_val, db_min, db_max
    global analyzer_accum, analyzer_count, analyzer_start_time, analyzer_is_collecting, analyzer_results
    
    # 1. Initialize Modules
    btn = machine.Pin(config.BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
    disp = DisplayManager()
    audio = AudioProcessor()
    net = NetworkManager(disp)
    
    # 2. Connect Network
    net.connect()
    
    # 3. Helper Functions
    
    def start_analyzer():
        """Starts the 5s accumulation."""
        global analyzer_start_time, analyzer_accum, analyzer_count, analyzer_is_collecting
        # Reset Accumulator with zeros based on sample length (FFT size / 2)
        fft_bins = int(config.SAMPLE_LENGTH / 2)
        analyzer_accum = [0] * fft_bins
        analyzer_count = 0
        analyzer_start_time = time.ticks_ms()
        analyzer_is_collecting = True
        disp.show_message("Analyzer Mode", "Measuring 5s...")

    def process_analyzer_step(magnitudes):
        """Adds current frame to accumulator."""
        global analyzer_accum, analyzer_count
        # Ensure lengths match before adding
        if len(magnitudes) == len(analyzer_accum):
            for i in range(len(magnitudes)):
                analyzer_accum[i] += magnitudes[i]
            analyzer_count += 1

    def finalize_analyzer():
        """Calculates final stats."""
        global analyzer_is_collecting, analyzer_results
        analyzer_is_collecting = False
        analyzer_results = audio.calculate_analyzer_stats(analyzer_accum, analyzer_count)
        # OLED update happens in main loop
        
    def cycle_vis_mode():
        """Cycles visualization type."""
        global vis_mode, db_min, db_max, analyzer_is_collecting
        
        analyzer_is_collecting = False
        vis_mode = (vis_mode + 1) % 4
        
        if vis_mode == 3: # dB Meter Reset
            db_min = 999
            db_max = -999
            
        if vis_mode == 2: # Start Analyzer
            start_analyzer()
        else:
            disp.show_message(VIS_MODE_NAMES[vis_mode], "Mode Selected")
            time.sleep(0.5)
            if output_mode == 1:
                disp.show_message("WEB MODE ACTIVE", net.ip_address)

    def toggle_output_mode():
        """Toggles between OLED and Web priority."""
        global output_mode, analyzer_is_collecting
        output_mode = (output_mode + 1) % 2
        analyzer_is_collecting = False
        
        if output_mode == 0:
            disp.show_message("OLED MODE", "WiFi Paused")
        else:
            disp.show_message("WEB MODE ACTIVE", net.ip_address)
        
        time.sleep(1.0)
        # Restart analyzer if we just switched into it
        if vis_mode == 2:
            start_analyzer()

    def get_json_data():
        """Generates JSON for the web client."""
        min_hz = 0
        max_hz = 0
        
        if vis_mode == 0: # Speech
            min_hz = 100
            max_hz = 1000
        elif vis_mode == 1: # Wide
            min_hz = 0
            max_hz = int(audio.max_freq)
        
        # Analyzer Data
        ana_max, ana_min, ana_avg = analyzer_results
        elapsed = 0
        if analyzer_is_collecting:
             elapsed = time.ticks_diff(time.ticks_ms(), analyzer_start_time)
             remaining = (ANALYZER_DURATION_MS - elapsed) // 1000
        else:
             remaining = 0

        parts = [
            f'"modeName":"{VIS_MODE_NAMES[vis_mode]}"',
            f'"minHz":"{min_hz}"',
            f'"maxHz":"{max_hz}"',
            # DB Data
            f'"dbValue":"{latest_db_val:.1f}"',
            f'"dbMin":"{db_min:.0f}"',
            f'"dbMax":"{db_max:.0f}"',
            # Analyzer Data
            f'"anaMax":"{ana_max}"',
            f'"anaMin":"{ana_min}"',
            f'"anaAvg":"{ana_avg:.0f}"',
            f'"analyzerTime":"{remaining}"',
            f'"analyzerStatus":"{"COLLECTING" if analyzer_is_collecting else "REPORT"}"'
        ]
        
        mag_str = ','.join([f"{m:.0f}" for m in latest_mags])
        parts.append(f'"magnitudes":[{mag_str}]')
        
        return '{' + ','.join(parts) + '}'

    print("System Running. Hold button 1s to switch Output Mode.")
    disp.show_message("Ready!", "Hold Btn: Web/OLED")
    time.sleep(1)

    # 4. Main Loop
    while True:
        try:
            current_time = time.ticks_ms()
            
            # --- INPUT HANDLING ---
            if btn.value() == 0:
                press_start = current_time
                while btn.value() == 0: time.sleep(0.05)
                press_duration = time.ticks_diff(time.ticks_ms(), press_start)
                if press_duration > 800: toggle_output_mode()
                else: cycle_vis_mode()
                    
            # --- ANALYZER TIMEOUT ---
            if analyzer_is_collecting:
                elapsed = time.ticks_diff(current_time, analyzer_start_time)
                if elapsed >= ANALYZER_DURATION_MS:
                    finalize_analyzer()

            # --- AUDIO READING ---
            raw = audio.read_audio()
            mags = audio.get_magnitudes(raw) 

            # --- MODE 0: OLED PRIORITY ---
            if output_mode == 0:
                if vis_mode == 0:   # Speech
                    bar_mags = audio.calculate_display_bars(mags, 100, 1000, config.SPEECH_BARS)
                    disp.draw_spectrum(bar_mags, 100, 1000, "Speech Mode")
                
                elif vis_mode == 1: # Wide
                    bar_mags = audio.calculate_display_bars(mags, 0, audio.max_freq, config.OLED_WIDTH)
                    disp.draw_spectrum(bar_mags, 0, audio.max_freq, "Wide Range")
                
                elif vis_mode == 2: # Analyzer 
                    if analyzer_is_collecting:
                        process_analyzer_step(mags)
                        # Visual bar for progress
                        elapsed = time.ticks_diff(current_time, analyzer_start_time)
                        bar_w = int((elapsed / ANALYZER_DURATION_MS) * 128)
                        disp.oled.fill(0)
                        disp.oled.text("Measuring...", 10, 10)
                        disp.oled.rect(0, 30, 128, 10, 1)
                        disp.oled.fill_rect(0, 30, bar_w, 10, 1)
                        disp.oled.show()
                    else:
                        # Show Report
                        max_f, min_f, avg_v = analyzer_results
                        disp.draw_analyzer_stats(max_f, min_f, avg_v)
                
                elif vis_mode == 3: # dB Meter
                    db = audio.calculate_db(raw)
                    if db > db_max: db_max = db
                    if db < db_min: db_min = db
                    disp.draw_db_meter(db, db_min, db_max)
                
            # --- MODE 1: WEB PRIORITY ---
            else:
                if vis_mode == 0: latest_mags = audio.calculate_display_bars(mags, 100, 1000, config.SPEECH_BARS)
                elif vis_mode == 1: latest_mags = audio.calculate_display_bars(mags, 0, audio.max_freq, config.OLED_WIDTH)
                
                elif vis_mode == 2: # Analyzer
                    if analyzer_is_collecting:
                        process_analyzer_step(mags)
                    
                    latest_mags = [] # Don't show bars in analyzer mode
                    if not analyzer_is_collecting:
                        disp.show_message("WEB REPORT", "Check Browser")
                    else:
                        disp.show_message("WEB ACTIVE", "Measuring...")

                elif vis_mode == 3: # dB Meter
                    db = audio.calculate_db(raw)
                    if db > db_max: db_max = db
                    if db < db_min: db_min = db
                    latest_db_val = db
                    latest_mags = []

                # Handle Network
                net.handle_request(get_json_data, cycle_vis_mode)

        except Exception as e:
            print(f"Error: {e}")
            disp.show_message("Error", str(e)[:16])
            time.sleep(2)

if __name__ == "__main__":
    main()
