import machine
import time
import config
from audio_processor import AudioProcessor
from display_manager import DisplayManager
from network_manager import NetworkManager

# --- Global State ---
# vis_mode: 0=Speech, 1=Wide, 2=dB
vis_mode = 0 
VIS_MODE_NAMES = ["Speech", "Wide", "dB Meter"]

# output_mode: 0=OLED Priority (Fast), 1=Web Priority (WiFi On)
output_mode = 0 
OUTPUT_NAMES = ["OLED Priority", "Web Priority"]

# Data containers for Web JSON
latest_mags = []
latest_db_val = 0.0
db_min = 999
db_max = -999

def main():
    global vis_mode, output_mode, latest_mags, latest_db_val, db_min, db_max
    
    # 1. Initialize Modules
    btn = machine.Pin(config.BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
    disp = DisplayManager()
    audio = AudioProcessor()
    net = NetworkManager(disp)
    
    # 2. Connect Network (Initial setup)
    net.connect()
    
    # 3. Helper Functions
    def cycle_vis_mode():
        """Short Press: Cycles visualization type."""
        global vis_mode, db_min, db_max
        vis_mode = (vis_mode + 1) % 3
        
        # Reset DB stats if entering dB mode
        if vis_mode == 2:
            db_min = 999
            db_max = -999
            
        # Show feedback briefly
        disp.show_message(VIS_MODE_NAMES[vis_mode], "Mode Selected")
        time.sleep(0.5)
        # If in Web Mode, restore the Web info screen
        if output_mode == 1:
            disp.show_message("WEB MODE ACTIVE", net.ip_address)

    def toggle_output_mode():
        """Long Press: Toggles between OLED and Web priority."""
        global output_mode
        output_mode = (output_mode + 1) % 2
        
        if output_mode == 0:
            disp.show_message("OLED MODE", "WiFi Paused")
        else:
            disp.show_message("WEB MODE ACTIVE", net.ip_address)
        
        time.sleep(1.0)

    def get_json_data():
        """Generates JSON for the web client."""
        min_hz = 100 if vis_mode == 0 else 0
        max_hz = 1000 if vis_mode == 0 else int(audio.max_freq)
        
        parts = [
            f'"modeName":"{VIS_MODE_NAMES[vis_mode]}"',
            f'"minHz":"{min_hz}"',
            f'"maxHz":"{max_hz}"',
            f'"dbValue":"{latest_db_val:.1f}"',
            f'"dbMin":"{db_min:.0f}"',
            f'"dbMax":"{db_max:.0f}"'
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
            # --- INPUT HANDLING (Short vs Long Press) ---
            if btn.value() == 0:
                press_start = time.ticks_ms()
                while btn.value() == 0:
                    time.sleep(0.05)
                
                press_duration = time.ticks_diff(time.ticks_ms(), press_start)
                
                if press_duration > 800: # Long Press (> 0.8s)
                    toggle_output_mode()
                else: # Short Press
                    cycle_vis_mode()

            # --- AUDIO READING ---
            raw = audio.read_audio()

            # --- MODE 0: OLED PRIORITY (Max Speed) ---
            if output_mode == 0:
                # 1. Calculate Data
                if vis_mode == 0:   # Speech
                    mags = audio.get_magnitudes(raw)
                    bar_mags = audio.calculate_display_bars(mags, 100, 1000, config.SPEECH_BARS)
                    disp.draw_spectrum(bar_mags, 100, 1000, "Speech Mode")
                
                elif vis_mode == 1: # Wide
                    mags = audio.get_magnitudes(raw)
                    bar_mags = audio.calculate_display_bars(mags, 0, audio.max_freq, config.OLED_WIDTH)
                    disp.draw_spectrum(bar_mags, 0, audio.max_freq, "Wide Range")
                
                elif vis_mode == 2: # dB Meter
                    db = audio.calculate_db(raw)
                    if db > db_max: db_max = db
                    if db < db_min: db_min = db
                    disp.draw_db_meter(db, db_min, db_max)
                
                # NOTE: We intentionally SKIP net.handle_request() here!
            
            # --- MODE 1: WEB PRIORITY (WiFi Enabled) ---
            else:
                # 1. Process Data (Just for JSON, no drawing)
                if vis_mode == 0:
                    mags = audio.get_magnitudes(raw)
                    latest_mags = audio.calculate_display_bars(mags, 100, 1000, config.SPEECH_BARS)
                elif vis_mode == 1:
                    mags = audio.get_magnitudes(raw)
                    latest_mags = audio.calculate_display_bars(mags, 0, audio.max_freq, config.OLED_WIDTH)
                elif vis_mode == 2:
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
