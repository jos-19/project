import machine
import time
import config
from audio_processor import AudioProcessor
from display_manager import DisplayManager
from network_manager import NetworkManager

# --- Global State ---
# vis_mode: 0=Speech, 1=Wide, 2=Band Monitor (5s), 3=dB Meter
vis_mode = 0 
VIS_MODE_NAMES = ["Speech", "Wide", "5s Bands", "dB Meter"]

# output_mode: 0=OLED Priority (Fast), 1=Web Priority (WiFi On)
output_mode = 0 
OUTPUT_NAMES = ["OLED Priority", "Web Priority"]

# Data containers for Web JSON
latest_mags = []
latest_db_val = 0.0
db_min = 999
db_max = -999
band_monitor_data = (0, 0, 0, 0) # (max_freq, max_mag, min_freq, min_mag)

# --- BAND MONITOR STATE ---
BAND_MONITOR_PERIOD_MS = 5000 # 5 seconds
band_data_collection = [] # Stores (max_freq, max_mag, min_mag) per frame
band_monitor_start_time = 0
band_monitor_is_collecting = False

def main():
    global vis_mode, output_mode, latest_mags, latest_db_val, db_min, db_max, band_monitor_data
    global band_monitor_start_time, band_data_collection, band_monitor_is_collecting
    
    # 1. Initialize Modules
    btn = machine.Pin(config.BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
    disp = DisplayManager()
    audio = AudioProcessor()
    net = NetworkManager(disp)
    
    # 2. Connect Network (Initial setup)
    net.connect()
    
    # 3. Helper Functions
    
    def start_band_monitor():
        """Starts the 5s data collection."""
        global band_monitor_start_time, band_data_collection, band_monitor_is_collecting
        band_data_collection = []
        band_monitor_start_time = time.ticks_ms()
        band_monitor_is_collecting = True
        disp.show_message("5s Band Monitor", "Collecting Data...")

    def finalize_band_monitor(current_time):
        """Processes collected data and sets final results."""
        global band_monitor_data, band_monitor_is_collecting
        
        band_monitor_is_collecting = False
        disp.show_message("5s Band Monitor", "Processing...")
        
        if not band_data_collection:
            band_monitor_data = (0, 0, 0, 0)
        else:
            # max_freq index: 0, max_mag index: 1, min_mag index: 2
            
            # Find the overall max magnitude and its corresponding frequency
            max_mag_entry = max(band_data_collection, key=lambda item: item[1])
            final_max_freq = max_mag_entry[0]
            final_max_mag = max_mag_entry[1]

            # Find the overall min magnitude and its corresponding frequency
            # Note: We look for the entry with the *lowest* min_mag (item[2])
            min_mag_entry = min(band_data_collection, key=lambda item: item[2])
            final_min_freq = min_mag_entry[3] # Index 3 stores min_freq
            final_min_mag = min_mag_entry[2]
            
            band_monitor_data = (final_max_freq, final_max_mag, final_min_freq, final_min_mag)
        
        # Display/Web will now show the final static result
        
    def cycle_vis_mode():
        """Short Press: Cycles visualization type."""
        global vis_mode, db_min, db_max, band_monitor_is_collecting
        
        # Stop collection if running
        band_monitor_is_collecting = False
        
        # Cycle through 4 modes
        vis_mode = (vis_mode + 1) % 4
        
        # Reset DB stats if entering dB mode
        if vis_mode == 3: # Mode 3 is now dB Meter
            db_min = 999
            db_max = -999
            
        # Start new collection if entering Band Monitor mode
        if vis_mode == 2:
            start_band_monitor()
            
        # Show feedback briefly
        disp.show_message(VIS_MODE_NAMES[vis_mode], "Mode Selected")
        time.sleep(0.5)
        # If in Web Mode, restore the Web info screen
        if output_mode == 1 and vis_mode != 2: # Don't overwrite collecting message
            disp.show_message("WEB MODE ACTIVE", net.ip_address)

    def toggle_output_mode():
        """Long Press: Toggles between OLED and Web priority."""
        global output_mode, band_monitor_is_collecting
        output_mode = (output_mode + 1) % 2
        
        # Reset Band Monitor state on output mode change
        band_monitor_is_collecting = False
        
        if output_mode == 0:
            disp.show_message("OLED MODE", "WiFi Paused")
        else:
            disp.show_message("WEB MODE ACTIVE", net.ip_address)
        
        time.sleep(1.0)
        # Restart collection if web mode is enabled and vis_mode is 2
        if output_mode == 1 and vis_mode == 2:
            start_band_monitor()

    def get_json_data():
        """Generates JSON for the web client."""
        # ... (JSON generation remains the same)
        min_hz = 0
        max_hz = 0
        
        if vis_mode == 0: # Speech
            min_hz = 100
            max_hz = 1000
        elif vis_mode == 1: # Wide
            min_hz = 0
            max_hz = int(audio.max_freq)
        
        max_freq, max_mag, min_freq, min_mag = band_monitor_data
        
        parts = [
            f'"modeName":"{VIS_MODE_NAMES[vis_mode]}"',
            f'"minHz":"{min_hz}"',
            f'"maxHz":"{max_hz}"',
            # DB Data
            f'"dbValue":"{latest_db_val:.1f}"',
            f'"dbMin":"{db_min:.0f}"',
            f'"dbMax":"{db_max:.0f}"',
            # Band Data
            f'"bandMaxFreq":"{max_freq}"',
            f'"bandMaxMag":"{max_mag:.0f}"',
            f'"bandMinFreq":"{min_freq}"',
            f'"bandMinMag":"{min_mag:.0f}"',
            f'"bandStatus":"{"COLLECTING" if band_monitor_is_collecting else "STATIC"}"' # NEW Status
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
            
            # --- INPUT HANDLING (Short vs Long Press) ---
            if btn.value() == 0:
                press_start = current_time
                while btn.value() == 0:
                    time.sleep(0.05)
                
                press_duration = time.ticks_diff(time.ticks_ms(), press_start)
                
                if press_duration > 800: # Long Press (> 0.8s)
                    toggle_output_mode()
                else: # Short Press
                    cycle_vis_mode()
                    
            # --- BAND MONITOR TIMEOUT CHECK (Runs in both Output Modes) ---
            if band_monitor_is_collecting and time.ticks_diff(current_time, band_monitor_start_time) >= BAND_MONITOR_PERIOD_MS:
                finalize_band_monitor(current_time)

            # --- AUDIO READING ---
            raw = audio.read_audio()
            mags = audio.get_magnitudes(raw) 

            # --- MODE 0: OLED PRIORITY (Max Speed) ---
            if output_mode == 0:
                if vis_mode == 0:   # Speech
                    bar_mags = audio.calculate_display_bars(mags, 100, 1000, config.SPEECH_BARS)
                    disp.draw_spectrum(bar_mags, 100, 1000, "Speech Mode")
                
                elif vis_mode == 1: # Wide
                    bar_mags = audio.calculate_display_bars(mags, 0, audio.max_freq, config.OLED_WIDTH)
                    disp.draw_spectrum(bar_mags, 0, audio.max_freq, "Wide Range")
                
                elif vis_mode == 2: # Band Monitor (5s)
                    if band_monitor_is_collecting:
                        # Collect data point for this frame
                        band_data_point = audio.analyze_bands(mags)
                        band_data_collection.append(band_data_point)
                        
                        # Show time remaining on screen
                        elapsed = time.ticks_diff(current_time, band_monitor_start_time)
                        remaining_s = (BAND_MONITOR_PERIOD_MS - elapsed) // 1000
                        disp.show_message("COLLECTING", f"{remaining_s}s remaining...")
                    else:
                        # Display final result
                        max_f, max_m, min_f, min_m = band_monitor_data
                        disp.draw_band_monitor(max_f, max_m, min_f, min_m)
                
                elif vis_mode == 3: # dB Meter
                    db = audio.calculate_db(raw)
                    if db > db_max: db_max = db
                    if db < db_min: db_min = db
                    disp.draw_db_meter(db, db_min, db_max)
                
            # --- MODE 1: WEB PRIORITY (WiFi Enabled) ---
            else:
                # 1. Process Data (Just for JSON, no drawing)
                if vis_mode == 0: # Speech
                    latest_mags = audio.calculate_display_bars(mags, 100, 1000, config.SPEECH_BARS)
                elif vis_mode == 1: # Wide
                    latest_mags = audio.calculate_display_bars(mags, 0, audio.max_freq, config.OLED_WIDTH)
                elif vis_mode == 2: # Band Monitor (5s)
                    if band_monitor_is_collecting:
                        # Collect data point for this frame
                        band_data_point = audio.analyze_bands(mags)
                        band_data_collection.append(band_data_point)
                    # When finalized, band_monitor_data is already updated
                    latest_mags = []
                elif vis_mode == 3: # dB Meter
                    db = audio.calculate_db(raw)
                    if db > db_max: db_max = db
                    if db < db_min: db_min = db
                    latest_db_val = db
                    latest_mags = []

                # 2. Handle Network (Every loop for responsiveness)
                net.handle_request(get_json_data, cycle_vis_mode)

        except Exception as e:
            print(f"Error: {e}")
            disp.show_message("Error", str(e)[:16])
            time.sleep(2)

if __name__ == "__main__":
    main()
