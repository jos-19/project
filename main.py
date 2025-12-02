import machine
import time
import config
from audio_processor import AudioProcessor
from display_manager import DisplayManager
from network_manager import NetworkManager

# Global State
current_mode = 0
MODE_NAMES = ["Speech", "Wide", "Analyzer", "dB Meter"]

# Data containers for Web JSON
latest_mags = []
latest_db_val = 0.0
db_min = 999
db_max = -999
latest_report_text = ""

# Analyzer state
analysis_start = 0
analysis_accum = []
analysis_count = 0
analysis_done = False

def main():
    global current_mode, latest_mags, latest_db_val, db_min, db_max
    global analysis_start, analysis_accum, analysis_count, analysis_done, latest_report_text

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
        global analysis_start, analysis_done, latest_report_text

        current_mode = (current_mode + 1) % 4  # now 4 modes
        # Reset stats on mode switch
        db_min = 999
        db_max = -999
        analysis_start = 0
        analysis_done = False
        latest_report_text = ""
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

        # Add report text (used for Analyzer mode)
        json_parts.append(f'"reportText":"{latest_report_text}"')

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
                while btn.value() == 0:
                    time.sleep(0.01)  # Debounce

            # Check Web
            net.handle_request(get_json_data, cycle_mode)

            # Audio Processing
            raw = audio.read_audio()

            if current_mode == 0:  # Speech Mode
                mags = audio.get_magnitudes(raw)
                bar_mags = audio.calculate_display_bars(mags, 100, 1000, config.SPEECH_BARS)
                latest_mags = bar_mags
                latest_report_text = ""
                disp.draw_spectrum(bar_mags, 100, 1000, "Speech Mode")

            elif current_mode == 1:  # Wide Mode
                mags = audio.get_magnitudes(raw)
                bar_mags = audio.calculate_display_bars(mags, 0, audio.max_freq, config.OLED_WIDTH)
                latest_mags = bar_mags
                latest_report_text = ""
                disp.draw_spectrum(bar_mags, 0, audio.max_freq, "Wide Range")

            elif current_mode == 2:  # Analyzer (most/least occupied)
                mags = audio.get_magnitudes(raw)

                # Start accumulation
                if analysis_start == 0:
                    analysis_start = time.time()
                    analysis_accum = [0] * len(mags)
                    analysis_count = 0
                    analysis_done = False

                if not analysis_done:
                    elapsed = time.time() - analysis_start

                    if elapsed < 5:
                        # Accumulate data
                        for i in range(len(mags)):
                            analysis_accum[i] += mags[i]
                        analysis_count += 1

                        # Update display with countdown
                        disp.show_message("Measuring...", f"Time: {5 - int(elapsed)}s")
                        latest_report_text = f"Measuring...|Time: {5 - int(elapsed)}s| "
                    else:
                        # Process results
                        analysis_done = True
                        if analysis_count == 0:
                            continue

                        avgs = [x / analysis_count for x in analysis_accum]
                        valid_data = avgs[config.IGNORE_LOW_BINS:]

                        if not valid_data:
                            continue

                        max_val = max(valid_data)
                        max_idx = valid_data.index(max_val) + config.IGNORE_LOW_BINS
                        max_hz = max_idx * audio.hz_per_bin

                        min_val = min(valid_data)
                        min_idx = valid_data.index(min_val) + config.IGNORE_LOW_BINS
                        min_hz = min_idx * audio.hz_per_bin

                        overall_avg = sum(valid_data) / len(valid_data)

                        # Display result on OLED
                        disp.oled.fill(0)
                        disp.oled.text("--- REPORT ---", 10, 0)
                        disp.oled.text(f"Max: {int(max_hz)} Hz", 0, 15)
                        disp.oled.text(f"Min: {int(min_hz)} Hz", 0, 30)
                        disp.oled.text(f"Avg: {int(overall_avg)}", 0, 45)
                        disp.oled.show()

                        # For web UI
                        latest_report_text = f"Max: {int(max_hz)} Hz|Min: {int(min_hz)} Hz|Avg: {int(overall_avg)}"
                        latest_mags = []  # clear bars since it's text-only

            elif current_mode == 3:  # dB Meter
                db = audio.calculate_db(raw)
                if db > db_max:
                    db_max = db
                if db < db_min:
                    db_min = db
                latest_db_val = db
                latest_mags = []
                latest_report_text = ""
                disp.draw_db_meter(db, db_min, db_max)

        except Exception as e:
            print(f"Error: {e}")
            disp.show_message("Error", str(e)[:16])
            time.sleep(2)

if __name__ == "__main__":
    main()
