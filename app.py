from flask import Flask, request, render_template_string
from collections import deque
import time

app = Flask(__name__)

# 存储最近 30 条历史记录
MAX_HISTORY = 30
history = {
    "labels": deque(maxlen=MAX_HISTORY),
    "temp": deque(maxlen=MAX_HISTORY),
    "co2": deque(maxlen=MAX_HISTORY),
    "pm25": deque(maxlen=MAX_HISTORY),
    "voc": deque(maxlen=MAX_HISTORY)
}

# 初始数据
latest_data = {
    "temp": "0", "hum": "0", "pres": "0", "alt": "0",
    "co2": "0", "voc": "0", "pm25": "0", "gas": "0"
}

def get_air_comment(co2, pm25, voc):
    try:
        c, p, v = float(co2), float(pm25), float(voc)
        if c > 1500 or p > 75 or v > 1000: return "⚠️ POOR: Open windows immediately!", "#e74c3c"
        if c > 1000 or p > 35 or v > 400: return "OK: Air is getting stale.", "#f1c40f"
        return "Excellent: Air is fresh.", "#2ecc71"
    except:
        return "Waiting for sensor data...", "#7f8c8d"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Pico 2W Ultimate Monitor</title>
    <meta http-equiv="refresh" content="15">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: auto; }
        .header { background: #1e293b; padding: 20px; border-radius: 15px; margin-bottom: 20px; border-top: 5px solid {{ color }}; }
        .comment { font-size: 1.5em; font-weight: bold; color: {{ color }}; }
        
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; }
        .card { background: #1e293b; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        .card label { font-size: 0.8em; color: #94a3b8; display: block; margin-bottom: 5px; }
        .card span { font-size: 1.4em; font-weight: bold; color: #38bdf8; }
        
        .chart-container { background: #1e293b; padding: 20px; border-radius: 15px; margin-top: 25px; }
        h2 { margin-top: 0; font-size: 1.2em; color: #94a3b8; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="comment">{{ comment }}</div>
            <p>Environment Status Dashboard | {{ time }}</p>
        </div>

        <div class="grid">
            <div class="card"><label>🌡️ Temperature</label><span>{{temp}} °C</span></div>
            <div class="card"><label>💧 Humidity</label><span>{{hum}} %</span></div>
            <div class="card"><label>☁️ CO2 Level</label><span>{{co2}} ppm</span></div>
            <div class="card"><label>😷 PM 2.5</label><span>{{pm25}} µg/m³</span></div>
            <div class="card"><label>🧪 VOC Index</label><span>{{voc}} ppb</span></div>
            <div class="card"><label>⛰️ Altitude</label><span>{{alt}} m</span></div>
            <div class="card"><label>⏲️ Pressure</label><span>{{pres}} hPa</span></div>
            <div class="card"><label>🔥 Gas Raw</label><span>{{gas}}</span></div>
        </div>

        <div class="chart-container">
            <h2>Real-time Trends (30-cycle history)</h2>
            <canvas id="mainChart"></canvas>
        </div>
    </div>

    <script>
        const ctx = document.getElementById('mainChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: {{ labels|tojson }},
                datasets: [
                    {
                        label: 'CO2 (ppm)',
                        data: {{ history_co2|tojson }},
                        borderColor: '#38bdf8',
                        yAxisID: 'y_large',
                        tension: 0.3
                    },
                    {
                        label: 'VOC (ppb)',
                        data: {{ history_voc|tojson }},
                        borderColor: '#a855f7',
                        yAxisID: 'y_large',
                        tension: 0.3
                    },
                    {
                        label: 'Temp (°C)',
                        data: {{ history_temp|tojson }},
                        borderColor: '#fbbf24',
                        yAxisID: 'y_small',
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                interaction: { mode: 'index', intersect: false },
                scales: {
                    y_large: {
                        type: 'linear', position: 'left',
                        title: { display: true, text: 'CO2 / VOC' },
                        grid: { color: '#334155' }
                    },
                    y_small: {
                        type: 'linear', position: 'right',
                        title: { display: true, text: 'Temperature' },
                        grid: { drawOnChartArea: false }
                    },
                    x: { grid: { color: '#334155' } }
                }
            }
        });
    </script>
</body>
</html>
