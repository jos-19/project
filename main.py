import machine
import time
import config
from audio_processor import AudioProcessor
from display_manager import DisplayManager
from network_manager import NetworkManager

# Global State
current_mode = 0
MODE_NAMES = ["Speech", "Wide", "dB Meter"]

# Data containers for Web JSON
latest_mags = []
latest_db_val = 0.0
db_min = 999
db_max = -999

def main():
    global current_mode, latest_mags, latest_db_val, db_min, db_max
    
    # 1. Initialize Modules
    btn = machine.Pin(config.BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
    disp = DisplayManager()
    audio = AudioProcessor()
    net = NetworkManager(disp)
    
    # 2. Connect Network
    net.connect()
    
    # 3. Helper Functions
    def cycle_mode():
        global current_mode, db_min, db_max
        current_mode = (current_mode + 1) % 3
        # Reset DB stats on mode switch
        if current_mode == 2:
            db_min = 999
            db_max = -999
        disp.show_message("Switching to", MODE_NAMES[current_mode])
        time.sleep(0.5)

    def get_json_data():
        """Generates the JSON string for the web app."""
        min_hz_val = 0
        max_hz_val = 0
        
        # Determine frequency range based on mode
        if current_mode == 0: 
            min_hz_val = 100
            max_hz_val = 1000
        elif current_mode == 1: 
            min_hz_val = 0
            max_hz_val = int(audio.max_freq)
        
        # Build JSON parts
        json_parts = []
        json_parts.append(f'"modeName":"{MODE_NAMES[current_mode]}"')
        json_parts.append(f'"minHz":"{min_hz_val}"')
        json_parts.append(f'"maxHz":"{max_hz_val}"')
        
        # DB Data
        json_parts.append(f'"dbValue":"{latest_db_val:.1f}"')
        json_parts.append(f'"dbMin":"{db_min:.0f}"')
        json_parts.append(f'"dbMax":"{db_max:.0f}"')
        
        # Spectrum Data
        mag_str = ','.join([f"{m:.0f}" for m in latest_mags])
        json_parts.append(f'"magnitudes":[{mag_str}]')
        
        return '{' + ','.join(json_parts) + '}'

    print("System Running...")
    
    # 4. Main Loop
    while True:
        try:
            # Check Button
            if btn.value() == 0:
                cycle_mode()
                while btn.value() == 0: time.sleep(0.01) # Debounce
                
            # Check Web
            net.handle_request(get_json_data, cycle_mode)
            
            # Audio Processing
            raw = audio.read_audio()
            
            if current_mode == 0: # Speech Mode (100Hz - 1000Hz)
                mags = audio.get_magnitudes(raw)
                bar_mags = audio.calculate_display_bars(mags, 100, 1000, config.SPEECH_BARS)
                latest_mags = bar_mags # Store for web
                disp.draw_spectrum(bar_mags, 100, 1000, "Speech Mode")
                
            elif current_mode == 1: # Wide Mode (0Hz - Max)
                mags = audio.get_magnitudes(raw)
                bar_mags = audio.calculate_display_bars(mags, 0, audio.max_freq, config.OLED_WIDTH)
                latest_mags = bar_mags # Store for web
                disp.draw_spectrum(bar_mags, 0, audio.max_freq, "Wide Range")
                
            elif current_mode == 2: # dB Meter
                db = audio.calculate_db(raw)
                if db > db_max: db_max = db
                if db < db_min: db_min = db
                latest_db_val = db # Store for web
                latest_mags = []   # Clear graph for web
                disp.draw_db_meter(db, db_min, db_max)

        except Exception as e:
            print(f"Error: {e}")
            disp.show_message("Error", str(e)[:16])
            time.sleep(2)

if __name__ == "__main__":
    main()
