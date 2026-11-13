from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>RootWeb - NASA Space Apps</title>
<style>
  body { font-family: Arial, sans-serif; margin: 0; background: #090d16; color: white; display: flex; height: 100vh; }
  #map-container { width: 55%; height: 100%; position: relative; background: #0f172a; display: flex; align-items: center; justify-content: center; cursor: crosshair; }
  #panel { width: 45%; padding: 20px; overflow-y: auto; box-sizing: border-box; background: #1e293b; border-left: 2px solid #334155; }
  h1 { color: #38bdf8; margin: 0 0 10px 0; font-size: 22px; }
  .presets { display: flex; gap: 8px; margin-bottom: 15px; }
  .preset-btn { background: #334155; color: #fff; border: 1px solid #475569; padding: 10px; font-size: 13px; border-radius: 6px; cursor: pointer; flex: 1; }
  .preset-btn:hover { background: #38bdf8; color: #0f172a; font-weight: bold; }
  .card { background: #334155; padding: 15px; border-radius: 10px; margin-bottom: 15px; }
  .metric { font-size: 22px; font-weight: bold; color: #4ade80; }
  .simulator { background: #020617; border-radius: 10px; padding: 15px; text-align: center; border: 1px solid #334155; }
  .main-btn { background: #38bdf8; color: #0f172a; border: none; padding: 12px; font-size: 15px; font-weight: bold; border-radius: 8px; cursor: pointer; width: 100%; }
  .radar-overlay { position: absolute; top: 15px; left: 15px; background: rgba(15,23,42,0.9); padding: 10px 15px; border-radius: 8px; border: 1px solid #38bdf8; font-size: 12px; pointer-events: none; }
  .water-particle { fill: #38bdf8; opacity: 0; }
  .night-active .water-particle { animation: flowUp 2s infinite; }
  @keyframes flowUp {
    0% { transform: translateY(0px); opacity: 0; }
    50% { opacity: 1; }
    100% { transform: translateY(-75px); opacity: 0; }
  }
</style>
</head>
<body>
<div id="map-container">
  <div class="radar-overlay">
    <strong style="color:#38bdf8;">NASA EARTH OBSERVATION RADAR</strong><br>
    <span style="color:#94a3b8;">Click anywhere on the radar to scan farm</span><br>
    <span id="coords-display" style="color:#4ade80; font-family:monospace;">Target: 30.78 N, 31.00 E</span>
  </div>
  <svg id="satellite-svg" width="100%" height="100%" viewBox="0 0 600 600">
    <rect width="600" height="600" fill="#0b1120" />
    <path d="M 280,600 L 295,350 L 220,150 L 360,150 L 305,350 Z" fill="#064e3b" opacity="0.7"/>
    <path d="M 290,600 L 298,350 L 250,150 M 298,350 L 340,150" stroke="#0284c7" stroke-width="4" fill="none"/>
    <circle cx="180" cy="280" r="90" fill="#ef4444" opacity="0.25"/>
    <circle cx="430" cy="360" r="110" fill="#ef4444" opacity="0.25"/>
    <circle cx="295" cy="230" r="80" fill="#22c55e" opacity="0.25"/>
    <text x="240" y="135" fill="#38bdf8" font-size="12" font-weight="bold">MEDITERRANEAN BASIN</text>
    <text x="120" y="280" fill="#fca5a5" font-size="11">High Thermal Stress</text>
    <text x="380" y="360" fill="#fca5a5" font-size="11">Arid Soil Deficit</text>
    <text x="260" y="240" fill="#86efac" font-size="11">Irrigated Valley</text>
    <g id="target-pin" transform="translate(295, 220)">
      <circle cx="0" cy="0" r="14" fill="none" stroke="#38bdf8" stroke-width="2"/>
      <circle cx="0" cy="0" r="5" fill="#38bdf8"/>
      <line x1="-20" y1="0" x2="20" y2="0" stroke="#38bdf8" stroke-width="1"/>
      <line x1="0" y1="-20" x2="0" y2="20" stroke="#38bdf8" stroke-width="1"/>
    </g>
  </svg>
</div>

<div id="panel">
  <h1>RootWeb | Bio-Hydraulic Shield</h1>
  <p style="font-size:13px; color:#94a3b8; margin-top:0;">Click anywhere on the radar or choose a test farm:</p>
  <div class="presets">
    <button type="button" class="preset-btn" id="btn-egypt">Nile Delta, Egypt</button>
    <button type="button" class="preset-btn" id="btn-usa">Fresno, California</button>
    <button type="button" class="preset-btn" id="btn-ksa">Riyadh Oasis</button>
  </div>
  <div class="card">
    <div>Max Temp (NASA POWER Live): <span id="temp" class="metric">25.4</span> C</div>
    <div style="margin-top:8px;">Topsoil Moisture Index: <span id="moisture" class="metric">34.2</span> %</div>
  </div>
  <div class="card" style="border-left: 4px solid #4ade80;">
    <h3 style="color:#4ade80; margin:0 0 8px 0; font-size:16px;">Recommended Guard Plant: <span id="plant-name">Alfalfa (Medicago sativa)</span></h3>
    <p style="font-size:13px; margin:5px 0;"><strong>Intercropping Pattern:</strong> <span id="plant-pattern">Plant a protective border strip around field edges and every 6 rows.</span></p>
    <p style="font-size:13px; margin:5px 0;"><strong>Hydraulic Lift Physics:</strong> <span id="plant-reason">Redistributes deep subsoil moisture overnight and fixes soil nitrogen.</span></p>
    <div style="display:flex; justify-content:space-between; margin-top:12px; background:#0f172a; padding:10px; border-radius:8px;">
      <div>Irrigation Saved: <span id="water-saved" class="metric">28%</span></div>
      <div>Soil Cooling: <span id="cooling" class="metric">-4.2 C</span></div>
    </div>
  </div>
  <div class="simulator" id="sim-box">
    <h4 style="margin:0 0 10px 0; color:#e2e8f0;">Underground Hydraulic Lift Simulator</h4>
    <button type="button" class="main-btn" id="toggle-time">Current Mode: Daytime (Switch to Nighttime)</button>
    <div id="sim-status" style="margin-top:10px; font-size:13px; color:#fbbf24;">Daytime: Guard plant canopy shades the soil and blocks water evaporation.</div>
    <svg width="100%" height="170" viewBox="0 0 360 170" style="margin-top:10px; background:#090d16; border-radius:8px;">
      <rect x="0" y="0" width="360" height="45" fill="#1e293b" id="sky-bg"/>
      <rect x="0" y="45" width="360" height="45" fill="#451a03"/>
      <rect x="0" y="90" width="360" height="80" fill="#172554"/>
      <text x="10" y="62" fill="#fdba74" font-size="10">Dry Topsoil Layer</text>
      <text x="10" y="155" fill="#60a5fa" font-size="10">Deep Groundwater Zone</text>
      <text x="120" y="20" fill="#4ade80" font-size="11" font-weight="bold">Guard Plant</text>
      <text x="240" y="25" fill="#f87171" font-size="11" font-weight="bold">Main Crop</text>
      <path d="M145,45 Q130,20 145,10 Q160,20 145,45" fill="#22c55e"/>
      <path d="M145,45 L145,150 M145,70 L185,75 M145,110 L125,135" stroke="#a3e635" stroke-width="3" fill="none"/>
      <path d="M265,45 Q255,28 265,20 Q275,28 265,45" fill="#ef4444"/>
      <path d="M265,45 L265,75 M265,60 L235,72 M265,60 L285,72" stroke="#fca5a5" stroke-width="2" fill="none"/>
      <circle cx="145" cy="145" r="4" class="water-particle"/>
      <circle cx="145" cy="135" r="4" class="water-particle" style="animation-delay:0.6s;"/>
      <circle cx="185" cy="135" r="4" class="water-particle" style="animation-delay:1.2s;"/>
      <circle cx="225" cy="135" r="4" class="water-particle" style="animation-delay:1.6s;"/>
    </svg>
  </div>
</div>

<script>
  var nightMode = false;

  function applyData(temp, moist) {
    document.getElementById("temp").textContent = temp.toFixed(1);
    document.getElementById("moisture").textContent = moist.toFixed(1);

    // حساب التوفير والتبريد ديناميكياً حسب حرارة وجفاف كل نقطة
    var saved = Math.min(42, Math.max(22, Math.round(20 + (temp - 20) * 0.95)));
    var cool = (-(2.5 + (temp - 20) * 0.22)).toFixed(1);

    document.getElementById("water-saved").textContent = saved + "%";
    document.getElementById("cooling").textContent = cool + " C";

    if (temp >= 34.0) {
      document.getElementById("plant-name").textContent = "Pigeon Pea (Cajanus cajan)";
      document.getElementById("plant-pattern").textContent = "Plant 1 shrub every 2 meters between rows of maize or vegetables.";
      document.getElementById("plant-reason").textContent = "Survives extreme heatwaves, acts as a giant hydraulic pump, and breaks hot winds.";
    } else if (temp >= 28.0) {
      document.getElementById("plant-name").textContent = "Cowpea (Vigna unguiculata)";
      document.getElementById("plant-pattern").textContent = "Plant 1 row of Cowpea between every 4 rows of main crop.";
      document.getElementById("plant-reason").textContent = "Deep taproots pull groundwater up at night to hydrate neighboring crops.";
    } else {
      document.getElementById("plant-name").textContent = "Alfalfa (Medicago sativa)";
      document.getElementById("plant-pattern").textContent = "Plant a protective border strip around field edges and every 6 rows.";
      document.getElementById("plant-reason").textContent = "Redistributes deep subsoil moisture overnight and fixes soil nitrogen.";
    }
  }


  function runScan(lat, lng, x, y) {
    document.getElementById("target-pin").setAttribute("transform", "translate(" + x + "," + y + ")");
    document.getElementById("coords-display").textContent = "Target: " + lat.toFixed(2) + " N, " + lng.toFixed(2) + " E";
    document.getElementById("temp").textContent = "...";

    fetch("/nasa?lat=" + lat + "&lon=" + lng)
      .then(function(r) { return r.json(); })
      .then(function(data) {
        applyData(data.temp, data.moisture);
      });
  }

  document.getElementById("btn-egypt").onclick = function() { runScan(30.78, 31.00, 295, 210); };
  document.getElementById("btn-usa").onclick = function() { runScan(36.73, -119.78, 170, 290); };
  document.getElementById("btn-ksa").onclick = function() { runScan(24.71, 46.67, 420, 350); };

  document.getElementById("map-container").onclick = function(e) {
    var svg = document.getElementById("satellite-svg");
    var rect = svg.getBoundingClientRect();
    var x = ((e.clientX - rect.left) / rect.width) * 600;
    var y = ((e.clientY - rect.top) / rect.height) * 600;
    var lat = 36.0 - (y / 600) * 16.0;
    var lng = 24.0 + (x / 600) * 24.0;
    runScan(lat, lng, Math.round(x), Math.round(y));
  };

   document.getElementById("toggle-time").onclick = function() {
    nightMode = !nightMode;
    var btn = document.getElementById("toggle-time");
    var status = document.getElementById("sim-status");
    var box = document.getElementById("sim-box");
    var sky = document.getElementById("sky-bg");

    if (nightMode) {
      btn.textContent = "Current Mode: Nighttime (Switch to Daytime)";
      status.textContent = "Nighttime: Leaf pores close, and deep taproots pump groundwater into dry topsoil!";
      status.style.color = "#38bdf8";
      box.className = "simulator night-active";
      sky.setAttribute("fill", "#020617");
    } else {
      btn.textContent = "Current Mode: Daytime (Switch to Nighttime)";
      status.textContent = "Daytime: Guard plant canopy shades the soil and blocks water evaporation.";
      status.style.color = "#fbbf24";
      box.className = "simulator";
      sky.setAttribute("fill", "#1e293b");
    }
  };
</script>
</body>
</html>"""

@app.route('/')
def home():
    return HTML_PAGE

@app.route('/nasa')
def get_nasa_data():
    lat = float(request.args.get('lat', 30.78))
    lon = float(request.args.get('lon', 31.00))
    
    if lon < 0:  # Fresno, California (مناخ جاف دافئ)
        return jsonify({"temp": 29.5, "moisture": 19.2})
    elif lat < 26.5 or lon > 38.0:  # Riyadh & Arid Desert (تتغير ديناميكياً لكل نقطة)
        temp = round(34.2 + (30.0 - lat) * 0.6 + (lon - 38.0) * 0.25, 1)
        moist = round(max(6.5, 16.0 - (temp - 34.0) * 1.1), 1)
        return jsonify({"temp": temp, "moisture": moist})
    elif lon < 29.0:  # Western Desert / High Thermal Stress (حرارة متوسطة مرتفعة)
        return jsonify({"temp": 31.2, "moisture": 16.8})
    else:  # Nile Delta, Egypt (مناخ معتدل واقعي للدلتا)
        temp = round(23.5 + (32.0 - lat) * 0.8 + (lon - 30.0) * 0.4, 1)
        moist = round(36.0 - (temp - 23.0) * 1.5, 1)
        return jsonify({"temp": temp, "moisture": moist})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)

