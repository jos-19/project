import machine
from sh1106 import SH1106_I2C
import config

class DisplayManager:
    """
    Manages the OLED display via I2C.
    """
    
    def __init__(self):
        i2c = machine.I2C(0, scl=machine.Pin(config.I2C_SCL_PIN), 
                          sda=machine.Pin(config.I2C_SDA_PIN), freq=400000)
        try:
            self.oled = SH1106_I2C(i2c)
        except TypeError:
            self.oled = SH1106_I2C(config.OLED_WIDTH, config.OLED_HEIGHT, i2c)
        
        self.oled.fill(0)
        self.oled.text("System Init...", 10, 30)
        self.oled.show()

    def show_message(self, line1, line2=""):
        self.oled.fill(0)
        self.oled.text(line1, 0, 0)
        self.oled.text(line2, 0, 15)
        self.oled.show()

    def draw_spectrum(self, magnitudes, min_hz, max_hz, title):
        self.oled.fill(0)
        self.oled.text(title, 0, 0)
        
        count = len(magnitudes)
        if count == 0: 
            self.oled.show()
            return

        width = config.OLED_WIDTH / count 
        bar_bottom = 53
        
        for i, mag in enumerate(magnitudes):
            h = int((mag / 150) * config.GAIN)
            if h > (bar_bottom - 10): h = (bar_bottom - 10)
            
            x = int(i * width)
            if h > 0:
                w = int(width) - 1
                if w < 1: w = 1
                self.oled.fill_rect(x, bar_bottom - h, w, h, 1)

        self.oled.hline(0, bar_bottom + 1, 128, 1)
        self.oled.text(self._format_freq(min_hz), 0, 56)
        self.oled.text(self._format_freq(max_hz), 90, 56)
        self.oled.show()

    # --- RESTORED ANALYZER DISPLAY ---
    def draw_analyzer_stats(self, max_hz, min_hz, avg_val):
        self.oled.fill(0)
        self.oled.text("--- REPORT ---", 10, 0)
        self.oled.text(f"Max: {int(max_hz)} Hz", 0, 20)
        self.oled.text(f"Min: {int(min_hz)} Hz", 0, 35)
        self.oled.text(f"Avg: {int(avg_val)}", 0, 50)
        self.oled.show()

    def draw_db_meter(self, db_val, db_min, db_max):
        self.oled.fill(0)
        self.oled.text("dB Meter", 35, 0)
        self.oled.text(f"{db_val:.1f} dB", 35, 20)
        self.oled.text(f"Min:{db_min:.0f}", 0, 55)
        self.oled.text(f"Max:{db_max:.0f}", 80, 55)
        
        bar_w = int((db_val / 100) * 128)
        if bar_w > 128: bar_w = 128
        self.oled.fill_rect(0, 35, bar_w, 10, 1)
        self.oled.show()

    def _format_freq(self, hz):
        if hz >= 1000: return f"{hz/1000:.1f}k"
        return f"{int(hz)}"
