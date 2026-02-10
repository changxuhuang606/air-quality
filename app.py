from flask import Flask, request, render_template_string
from collections import deque
import time

app = Flask(__name__)

MAX_HISTORY = 20
history = {
    "labels": deque(maxlen=MAX_HISTORY),
    "temp": deque(maxlen=MAX_HISTORY),
    "co2": deque(maxlen=MAX_HISTORY),
    "pm25": deque(maxlen=MAX_HISTORY)
}

latest_data = {"temp": 0, "hum": 0, "co2": 0, "pm25": 0, "gas": 0}

def get_comment(co2, pm25):
    """根据数据生成语音/文字评语"""
    if co2 == 0: return "Waiting for data..."
    if co2 < 800 and pm25 < 35:
        return "Excellent: Fresh and clean air!"
    elif co2 < 1200 and pm25 < 75:
        return "Good: Air quality is acceptable."
    else:
        return "Warning: Poor air, please ventilate!"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Pico 2W Smart Monitor</title>
    <meta http-equiv="refresh" content="15">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #121212; color: white; text-align: center; margin: 0; }
        .container { max-width: 600px; margin: auto; padding: 20px; }
        .status-box { 
            background: #1e1e1e; padding: 20px; border-radius: 15px; 
            margin-bottom: 20px; border-bottom: 5px solid {{ color }};
        }
        .comment { font-size: 1.2em; font-weight: bold; color: {{ color }}; }
        .metric-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }
        .card { background: #252525; padding: 15px; border-radius: 10px; }
        .val { font-size: 1.3em; display: block; color: #00ffcc; }
        canvas { background: #1e1e1e; border-radius: 10px; padding: 10px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Live Air Analytics</h1>
        
        <div class="status-box">
            <div class="comment">{{ comment }}</div>
            <small>Last updated: {{ time }}</small>
        </div>

        <div class="metric-grid">
            <div class="card">Temp<span class="val">{{temp}}°C</span></div>
            <div class="card">Humidity<span class="val">{{hum}}%</span></div>
            <div class="card">CO2<span class="val">{{co2}} ppm</span></div>
            <div class="card">PM2.5<span class="val">{{pm25}} µg/m³</span></div>
        </div>

        <canvas id="airChart" width="400" height="200"></canvas>
    </div>

    <script>
        const ctx = document.getElementById('airChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: {{ labels|tojson }},
                datasets: [{
                    label: 'CO2 Level',
                    data: {{ history_co2|tojson }},
                    borderColor: '#00ffcc',
                    tension: 0.3,
                    fill: false
                },
                {
                    label: 'PM 2.5',
                    data: {{ history_pm25|tojson }},
                    borderColor: '#ff4444',
                    tension: 0.3,
                    fill: false
                }]
            },
            options: { responsive: true, scales: { y: { beginAtZero: false } } }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    co2 = int(latest_data['co2']) if latest_data['co2'] != 'Waiting...' else 0
    pm25 = float(latest_data['pm25']) if latest_data['pm25'] != 'Waiting...' else 0
    
    # 根据空气质量决定评语颜色
    color = "#2ecc71" if co2 < 1000 else "#f1c40f" if co2 < 1500 else "#e74c3c"
    
    return render_template_string(
        HTML_TEMPLATE, 
        **latest_data, 
        comment=get_comment(co2, pm25),
        color=color,
        time=time.strftime("%H:%M:%S"),
        labels=list(history["labels"]),
        history_co2=list(history["co2"]),
        history_pm25=list(history["pm25"])
    )

@app.route('/update')
def update():
    for key in latest_data:
        val = request.args.get(key if key != 'temp' else 't')
        if val:
            latest_data[key] = val
    
    # 更新历史记录用于画图
    current_time = time.strftime("%H:%M")
    history["labels"].append(current_time)
    history["co2"].append(float(latest_data["co2"]))
    history["pm25"].append(float(latest_data["pm25"]))
    
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)