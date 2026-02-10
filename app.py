from flask import Flask, request, render_template_string
from collections import deque
import time

app = Flask(__name__)

# Store last 30 data points for the graph
MAX_HISTORY = 30
history = {
    "labels": deque(maxlen=MAX_HISTORY),
    "temp": deque(maxlen=MAX_HISTORY),
    "co2": deque(maxlen=MAX_HISTORY),
    "voc": deque(maxlen=MAX_HISTORY)
}

# Current sensor values
latest_data = {
    "temp": "0", "hum": "0", "pres": "0", "alt": "0",
    "co2": "0", "voc": "0", "pm25": "0", "gas": "0"
}

def get_air_quality_info(co2, pm25, voc):
    try:
        c, p, v = float(co2), float(pm25), float(voc)
        if c > 1500 or p > 75 or v > 600:
            return "⚠️ POOR: Open windows!", "#e74c3c" # Red
        if c > 1000 or p > 35 or v > 250:
            return "OK: Air is getting stale.", "#f1c40f" # Yellow
        return "Excellent: Air is fresh.", "#2ecc71" # Green
    except:
        return "Waiting for Pico...", "#7f8c8d"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Global Air Monitor</title>
    <meta http-equiv="refresh" content="15">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: auto; }
        .header { background: #1e293b; padding: 20px; border-radius: 15px; margin-bottom: 20px; border-top: 8px solid {{ color }}; }
        .comment { font-size: 1.6em; font-weight: bold; color: {{ color }}; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 15px; }
        .card { background: #1e293b; padding: 15px; border-radius: 12px; border: 1px solid #334155; }
        .card label { font-size: 0.8em; color: #94a3b8; display: block; margin-bottom: 5px; }
        .card span { font-size: 1.4em; font-weight: bold; color: #38bdf8; }
        .chart-container { background: #1e293b; padding: 20px; border-radius: 15px; margin-top: 25px; border: 1px solid #334155; }
        h2 { margin: 0 0 15px 0; font-size: 1.1em; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="comment">{{ comment }}</div>
            <p>Pico 2W Station | Last Sync: {{ time }}</p>
        </div>

        <div class="grid">
            <div class="card"><label>Temperature</label><span>{{temp}} °C</span></div>
            <div class="card"><label>Humidity</label><span>{{hum}} %</span></div>
            <div class="card"><label>CO2 Level</label><span>{{co2}} ppm</span></div>
            <div class="card"><label>PM 2.5</label><span>{{pm25}} µg/m³</span></div>
            <div class="card"><label>VOC Index</label><span>{{voc}} ppb</span></div>
            <div class="card"><label>Altitude</label><span>{{alt}} m</span></div>
            <div class="card"><label>Pressure</label><span>{{pres}} hPa</span></div>
            <div class="card"><label>Gas Raw</label><span>{{gas}}</span></div>
        </div>

        <div class="chart-container">
            <h2>Environment Trends</h2>
            <canvas id="airChart"></canvas>
        </div>
    </div>

    <script>
        const ctx = document.getElementById('airChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: {{ labels|tojson }},
                datasets: [
                    {
                        label: 'CO2 (ppm)',
                        data: {{ history_co2|tojson }},
                        borderColor: '#38bdf8',
                        backgroundColor: '#38bdf833',
                        yAxisID: 'y_large',
                        tension: 0.3,
                        fill: true
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
                scales: {
                    y_large: {
                        type: 'linear', position: 'left',
                        grid: { color: '#334155' },
                        title: { display: true, text: 'Gases' }
                    },
                    y_small: {
                        type: 'linear', position: 'right',
                        grid: { drawOnChartArea: false },
                        title: { display: true, text: 'Temp' }
                    }
                }
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    msg, col = get_air_quality_info(latest_data['co2'], latest_data['pm25'], latest_data['voc'])
    return render_template_string(
        HTML_TEMPLATE, 
        **latest_data, 
        comment=msg, 
        color=col,
        time=time.strftime("%H:%M:%S"),
        labels=list(history["labels"]),
        history_co2=list(history["co2"]),
        history_temp=list(history["temp"]),
        history_voc=list(history["voc"])
    )

@app.route('/update')
def update():
    # Capture parameters from Pico
    for key in ['hum', 'pres', 'alt', 'co2', 'voc', 'pm25', 'gas']:
        val = request.args.get(key)
        if val: latest_data[key] = val
    
    # Handle temperature separately because Pico sends it as 't'
    temp_val = request.args.get('t')
    if temp_val: latest_data['temp'] = temp_val

    # Update history for charts
    current_time = time.strftime("%H:%M")
    history["labels"].append(current_time)
    history["temp"].append(float(latest_data["temp"]))
    history["co2"].append(float(latest_data["co2"]))
    history["voc"].append(float(latest_data["voc"]))
    
    return "Data Received", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
