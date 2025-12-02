import network
import usocket as socket
import time
import config

# --- FULL HTML APP ---
# Updated to handle the Band Monitor Mode and the new status
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>ESP32 Spectrum</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #111827; color: #fff; text-align: center; margin: 0; padding: 20px;}
        h1 { font-size: 1.5rem; margin-bottom: 10px; color: #10b981; }
        .card { background: #1f2937; border-radius: 12px; padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); max-width: 400px; margin: 0 auto; position: relative; min-height: 300px;}
        #canvas-container { position: relative; margin: 10px 0; border: 1px solid #374151; border-radius: 4px; overflow: hidden; height: 220px;}
        canvas { display: block; width: 100%; height: 100%; background: #000; }
        .mode-view { 
            display: none; 
            flex-direction: column; 
            justify-content: center; 
            align-items: center; 
            height: 220px; 
            background: #1f2937; 
            border-radius: 4px; 
            border: 1px solid #374151; 
            padding: 10px;
        }
        
        /* dB Meter Styles */
        #db-view { display: none; }
        .db-main { font-size: 3.5rem; font-weight: bold; color: #facc15; }
        .db-stats { display: flex; gap: 20px; margin-top: 20px; color: #9ca3af; font-size: 1rem; }
        .db-bar-bg { width: 80%; height: 20px; background: #333; margin-top: 20px; border-radius: 10px; overflow: hidden; }
        .db-bar-fill { height: 100%; background: #facc15; width: 0%; transition: width 0.3s; }
        
        /* Band Monitor Styles */
        #band-view { display: none; }
        .band-row { display: flex; justify-content: space-between; width: 90%; margin: 8px 0; padding: 5px; background: #374151; border-radius: 4px;}
        .band-label { font-weight: bold; color: #10b981; }
        .band-value { color: #facc15; }
        #band-status { font-size: 1.2rem; margin-bottom: 10px; font-weight: 500;}

        .controls { margin-top: 20px; display: flex; justify-content: center; gap: 10px; }
        button { background: #3b82f6; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-size: 1rem; font-weight: bold; cursor: pointer; transition: background 0.2s; }
        .info { margin-top: 10px; font-size: 0.9rem; color: #9ca3af; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Audio Analyzer</h1>
        <div id="canvas-container"><canvas id="analyzerCanvas" width="350" height="220"></canvas></div>
        
        <div id="db-view" class="mode-view">
            <div class="db-main" id="db-val">0.0 dB</div>
            <div class="db-bar-bg"><div class="db-bar-fill" id="db-fill"></div></div>
            <div class="db-stats"><span id="db-min">Min: 0</span><span id="db-max">Max: 0</span></div>
        </div>
        
        <div id="band-view" class="mode-view">
            <div id="band-status">Awaiting Data...</div>
            <div class="band-row">
                <span class="band-label">Max Frequency:</span>
                <span class="band-value" id="band-max-freq">N/A</span>
            </div>
            <div class="band-row">
                <span class="band-label">Max Magnitude:</span>
                <span class="band-value" id="band-max-mag">N/A</span>
            </div>
            <div class="band-row">
                <span class="band-label">Min Frequency:</span>
                <span class="band-value" id="band-min-freq">N/A</span>
            </div>
            <div class="band-row">
                <span class="band-label">Min Magnitude:</span>
                <span class="band-value" id="band-min-mag">N/A</span>
            </div>
        </div>
        
        <div class="info" id="status">Connecting...</div>
        <div class="controls"><button onclick="switchMode()">Next Mode &#8635;</button></div>
    </div>
    <script>
        const canvas = document.getElementById('analyzerCanvas');
        const canvasContainer = document.getElementById('canvas-container');
        const dbView = document.getElementById('db-view');
        const bandView = document.getElementById('band-view');
        const ctx = canvas.getContext('2d');
        const FIXED_MAX_MAG = 3000; 

        // Helper to format Hz values
        function formatFreq(hz) {
            if (hz >= 1000) return (hz / 1000).toFixed(1) + 'k Hz';
            return hz + ' Hz';
        }

        async function fetchData() {
            try {
                const response = await fetch('/api/data');
                if (!response.ok) throw new Error('Network err');
                const data = await response.json();
                updateUI(data);
                document.getElementById('status').textContent = data.modeName + (data.bandStatus === "COLLECTING" ? " (Collecting)" : "");
            } catch (error) { document.getElementById('status').textContent = 'Disconnected...'; }
        }

        async function switchMode() { try { await fetch('/api/switch_mode'); } catch (e) {} }

        function hideAllViews() {
            canvasContainer.style.display = 'none';
            dbView.style.display = 'none';
            bandView.style.display = 'none';
        }

        function updateUI(data) {
            hideAllViews();
            
            if (data.modeName === "dB Meter") {
                dbView.style.display = 'flex';
                document.getElementById('db-val').textContent = data.dbValue + " dB";
                document.getElementById('db-min').textContent = "Min: " + data.dbMin;
                document.getElementById('db-max').textContent = "Max: " + data.dbMax;
                let pct = parseFloat(data.dbValue); if (pct > 100) pct = 100;
                document.getElementById('db-fill').style.width = pct + "%";
                return;
            }
            
            if (data.modeName === "5s Bands") {
                bandView.style.display = 'flex';
                const statusText = data.bandStatus === "COLLECTING" ? "COLLECTING DATA (5s)" : "FINAL RESULTS";
                document.getElementById('band-status').textContent = statusText;

                document.getElementById('band-max-freq').textContent = formatFreq(parseInt(data.bandMaxFreq));
                document.getElementById('band-max-mag').textContent = data.bandMaxMag;
                document.getElementById('band-min-freq').textContent = formatFreq(parseInt(data.bandMinFreq));
                document.getElementById('band-min-mag').textContent = data.bandMinMag;
                
                // --- FIX START ---
                // OLD LINE: return;
                // NEW: Remove the return statement so it continues to draw the spectrum below
                // --- FIX END ---
            }

            // Spectrum Modes (Speech and Wide) - AND NOW 5S BANDS TOO
            canvasContainer.style.display = 'block';
            drawSpectrum(data);

        function drawSpectrum(data) {
            const w = canvas.width; const h = canvas.height; const bottomMargin = 20; const graphH = h - bottomMargin;
            ctx.clearRect(0, 0, w, h);
            ctx.fillStyle = '#10b981';
            const barCount = data.magnitudes.length;
            if (barCount > 0) {
                const barWidth = w / barCount;
                data.magnitudes.forEach((mag, i) => {
                    let height = (mag / FIXED_MAX_MAG) * graphH;
                    if (height > graphH) height = graphH;
                    ctx.fillRect(i * barWidth, graphH - height, barWidth - 1, height);
                });
            }
            ctx.fillStyle = '#9ca3af'; ctx.font = '12px sans-serif';
            ctx.textAlign = 'left'; ctx.fillText(formatFreq(parseInt(data.minHz)), 5, h - 5);
            ctx.textAlign = 'right'; ctx.fillText(formatFreq(parseInt(data.maxHz)), w - 5, h - 5);
        }
        
        setInterval(fetchData, 300); 
    </script>
</body>
</html>
"""

class NetworkManager:
    """Handles Wi-Fi and Web Server."""
    def __init__(self, display_ref):
        self.wlan = network.WLAN(network.STA_IF)
        self.server_socket = None
        self.ip_address = "N/A"
        self.display = display_ref 

    def connect(self):
        """Connects to WiFi and prints status to OLED."""
        self.display.show_message("Connecting WiFi", "Please wait...")
        self.wlan.active(True)
        self.wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        
        attempts = 0
        while not self.wlan.isconnected() and attempts < 10:
            time.sleep(1)
            attempts += 1
            
        if self.wlan.isconnected():
            self.ip_address = self.wlan.ifconfig()[0]
            self.display.show_message("IP Address:", self.ip_address)
            time.sleep(2)
            self._start_server()
            return True
        else:
            self.display.show_message("WiFi Failed", "Offline Mode")
            time.sleep(2)
            return False

    def _start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('', 80))
        self.server_socket.listen(1)
        self.server_socket.setblocking(False) 

    def handle_request(self, data_json_func, cycle_mode_func):
        if not self.server_socket: return
        try:
            conn, addr = self.server_socket.accept()
            conn.settimeout(3.0)
            request = str(conn.recv(1024))
            
            response = ""
            if '/api/switch_mode' in request:
                cycle_mode_func()
                response = 'HTTP/1.0 200 OK\r\n\r\nOK'
            elif '/api/data' in request:
                response = 'HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n' + data_json_func()
            else:
                response = 'HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n' + HTML_PAGE
            
            conn.send(response)
            conn.close()
        except OSError:
            pass
