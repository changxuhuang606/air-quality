from flask import Flask, request, render_template_string

app = Flask(__name__)

# Dictionary to store the latest sensor data
latest_data = {
    "temp": "Waiting...",
    "hum": "Waiting...",
    "co2": "Waiting...",
    "pm25": "Waiting...",
    "gas": "Waiting..."
}

# Simple HTML dashboard with one parameter per line
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Pico 2W Air Monitor</title>
    <meta http-equiv="refresh" content="10">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #1a1a1a; color: white; text-align: center; }
        .container { max-width: 400px; margin: 50px auto; }
        .metric-card { 
            background: #333; margin: 10px; padding: 20px; 
            border-radius: 12px; display: flex; justify-content: space-between;
            border-left: 5px solid #00ffcc;
        }
        .label { color: #aaa; font-size: 0.9em; }
        .value { font-size: 1.4em; font-weight: bold; color: #00ffcc; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Air Quality Dashboard</h1>
        <div class="metric-card"><span class="label">Temperature</span><span class="value">{{temp}} °C</span></div>
        <div class="metric-card"><span class="label">Humidity</span><span class="value">{{hum}} %</span></div>
        <div class="metric-card"><span class="label">CO2 Level</span><span class="value">{{co2}} ppm</span></div>
        <div class="metric-card"><span class="label">PM 2.5</span><span class="value">{{pm25}} ug/m3</span></div>
        <div class="metric-card"><span class="label">Gas Sensor</span><span class="value">{{gas}}</span></div>
        <p style="font-size: 0.7em; color: #555;">Updates automatically every 10s</p>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, **latest_data)

@app.route('/update')
def update():
    # Update global data from URL parameters
    latest_data["temp"] = request.args.get('t', latest_data["temp"])
    latest_data["hum"] = request.args.get('h', latest_data["hum"])
    latest_data["co2"] = request.args.get('co2', latest_data["co2"])
    latest_data["pm25"] = request.args.get('pm25', latest_data["pm25"])
    latest_data["gas"] = request.args.get('gas', latest_data["gas"])
    return "Data Received", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)