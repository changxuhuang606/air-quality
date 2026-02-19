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
            return "⚠️ POOR: Open windows!", "#e74c3c"  # Red
        if c > 1000 or p > 35 or v > 250:
            return "OK: Air is getting stale.", "#f1c40f"  # Yellow
        return "Excellent: Air is fresh.", "#2ecc71"  # Green
    except:
        return "Waiting for Pico...", "#7f8c8d"

def safe_float(x, default=0.0):
    try:
        return float(x)
    except:
        return default

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Global Air Monitor</title>
    <meta http-equiv="refresh" content="15">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root{
            --bg: #f6f8fc;
            --panel: #ffffff;
            --text: #0f172a;
            --muted: #64748b;
            --border: #e5e7eb;
            --shadow: 0 10px 30px rgba(2, 6, 23, .08);
            --radius: 16px;

            --blue: #2563eb;
            --violet: #7c3aed;
            --amber: #f59e0b;
            --cyan: #06b6d4;
        }

        * { box-sizing: border-box; }
        body {
            font-family: ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;
            background: radial-gradient(1200px 600px at 10% -10%, rgba(37,99,235,.15), transparent 55%),
                        radial-gradient(900px 500px at 90% 0%, rgba(124,58,237,.12), transparent 55%),
                        var(--bg);
            color: var(--text);
            margin: 0;
            padding: 22px;
        }

        .container { max-width: 980px; margin: 0 auto; }

        .header {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 18px 18px 16px;
            box-shadow: var(--shadow);
            position: relative;
            overflow: hidden;
        }
        .header:before{
            content:"";
            position:absolute; left:0; top:0; right:0; height:8px;
            background: linear-gradient(90deg, {{ color }}, rgba(37,99,235,.25));
        }

        .title-row{
            display:flex;
            align-items:flex-start;
            justify-content:space-between;
            gap: 12px;
        }
        .brand{
            display:flex; flex-direction:column; gap:6px;
        }
        .comment {
            font-size: 1.25em;
            font-weight: 750;
            line-height: 1.2;
            color: var(--text);
        }
        .sub {
            color: var(--muted);
            font-size: .95em;
        }
        .pill {
            display:inline-flex;
            align-items:center;
            gap:8px;
            padding: 8px 10px;
            border-radius: 999px;
            border: 1px solid var(--border);
            background: #f8fafc;
            color: var(--muted);
            font-size: .9em;
            white-space: nowrap;
        }
        .dot{
            width:10px; height:10px; border-radius:50%;
            background: {{ color }};
            box-shadow: 0 0 0 4px rgba(0,0,0,.04);
        }

        .grid {
            margin-top: 16px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
            gap: 14px;
        }

        .card {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 14px 14px 12px;
            box-shadow: 0 6px 18px rgba(2, 6, 23, .06);
        }
        .card label {
            font-size: 0.78em;
            color: var(--muted);
            display: block;
            margin-bottom: 7px;
            letter-spacing: .02em;
            text-transform: uppercase;
        }
        .value-row{
            display:flex;
            align-items: baseline;
            justify-content: space-between;
            gap: 10px;
        }
        .card span {
            font-size: 1.55em;
            font-weight: 800;
            color: #0b1220;
        }
        .unit {
            color: var(--muted);
            font-weight: 600;
            font-size: .95em;
        }

        .chart-container {
            margin-top: 16px;
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 16px 16px 14px;
            box-shadow: var(--shadow);
        }
        h2 {
            margin: 0 0 10px 0;
            font-size: 0.95em;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: .12em;
        }
        canvas { width: 100% !important; height: 360px !important; }

        @media (max-width: 520px){
            body { padding: 14px; }
            canvas { height: 300px !important; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title-row">
                <div class="brand">
                    <div class="comment">{{ comment }}</div>
                    <div class="sub">Pico 2W Station · Auto refresh 15s</div>
                </div>
                <div class="pill"><span class="dot"></span> Last Updated: {{ time }}</div>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <label>Temperature</label>
                <div class="value-row"><span>{{temp}}</span><div class="unit">°C</div></div>
            </div>
            <div class="card">
                <label>Humidity</label>
                <div class="value-row"><span>{{hum}}</span><div class="unit">%</div></div>
            </div>
            <div class="card">
                <label>CO2</label>
                <div class="value-row"><span>{{co2}}</span><div class="unit">ppm</div></div>
            </div>
            <div class="card">
                <label>PM 2.5</label>
                <div class="value-row"><span>{{pm25}}</span><div class="unit">µg/m³</div></div>
            </div>
            <div class="card">
                <label>VOC</label>
                <div class="value-row"><span>{{voc}}</span><div class="unit">ppb</div></div>
            </div>
            <div class="card">
                <label>Altitude</label>
                <div class="value-row"><span>{{alt}}</span><div class="unit">m</div></div>
            </div>
            <div class="card">
                <label>Pressure</label>
                <div class="value-row"><span>{{pres}}</span><div class="unit">hPa</div></div>
            </div>
            <div class="card">
                <label>Gas Raw</label>
                <div class="value-row"><span>{{gas}}</span><div class="unit">&nbsp;</div></div>
            </div>
        </div>

        <div class="chart-container">
            <h2>Environment Trends</h2>
            <canvas id="airChart"></canvas>
        </div>
    </div>

    <script>
        // Improve rendering on high-DPI screens
        Chart.defaults.devicePixelRatio = Math.max(window.devicePixelRatio || 1, 2);

        const ctx = document.getElementById('airChart').getContext('2d');

        // Colors in rgba
        const cBlue   = 'rgba(37, 99, 235, 1)';
        const cBlueF  = 'rgba(37, 99, 235, .12)';
        const cViolet = 'rgba(124, 58, 237, 1)';
        const cVioletF= 'rgba(124, 58, 237, .08)';
        const cAmber  = 'rgba(245, 158, 11, 1)';

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: {{ labels|tojson }},
                datasets: [
                    {
                        label: 'CO2 (ppm)',
                        data: {{ history_co2|tojson }},
                        borderColor: cBlue,
                        backgroundColor: cBlueF,
                        yAxisID: 'y_large',
                        tension: 0.35,
                        fill: true,
                        borderWidth: 2.5,
                        pointRadius: 1.8,
                        pointHoverRadius: 4,
                        pointHitRadius: 10
                    },
                    {
                        label: 'VOC (ppb)',
                        data: {{ history_voc|tojson }},
                        borderColor: cViolet,
                        backgroundColor: cVioletF,
                        yAxisID: 'y_large',
                        tension: 0.35,
                        fill: false,
                        borderWidth: 2.2,
                        pointRadius: 1.8,
                        pointHoverRadius: 4,
                        pointHitRadius: 10
                    },
                    {
                        label: 'Temp (°C)',
                        data: {{ history_temp|tojson }},
                        borderColor: cAmber,
                        yAxisID: 'y_small',
                        tension: 0.35,
                        fill: false,
                        borderWidth: 2.2,
                        pointRadius: 1.8,
                        pointHoverRadius: 4,
                        pointHitRadius: 10
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            boxWidth: 10,
                            boxHeight: 10,
                            color: '#0f172a',
                            font: { size: 12, weight: '600' }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, .92)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        padding: 10,
                        displayColors: true
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(15, 23, 42, .06)' },
                        ticks: { color: '#64748b', maxRotation: 0, autoSkip: true }
                    },
                    y_large: {
                        type: 'linear',
                        position: 'left',
                        grid: { color: 'rgba(15, 23, 42, .06)' },
                        ticks: { color: '#64748b' },
                        title: { display: true, text: 'CO2 / VOC', color: '#64748b', font: { weight: '600' } },
                        suggestedMin: 0,
                        suggestedMax: 2000
                    },
                    y_small: {
                        type: 'linear',
                        position: 'right',
                        grid: { drawOnChartArea: false },
                        ticks: { color: '#64748b' },
                        title: { display: true, text: 'Temperature', color: '#64748b', font: { weight: '600' } },
                        suggestedMin: 0,
                        suggestedMax: 60
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
        if val is not None and val != "":
            latest_data[key] = val

    # Handle temperature separately because Pico sends it as 't'
    temp_val = request.args.get('t')
    if temp_val is not None and temp_val != "":
        latest_data['temp'] = temp_val

    # Update history for charts (robust to bad/empty values)
    current_time = time.strftime("%H:%M")
    history["labels"].append(current_time)
    history["temp"].append(safe_float(latest_data["temp"]))
    history["co2"].append(safe_float(latest_data["co2"]))
    history["voc"].append(safe_float(latest_data["voc"]))

    return "Data Received", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
