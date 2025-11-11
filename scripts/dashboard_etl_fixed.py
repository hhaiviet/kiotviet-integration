#!/usr/bin/env python3
"""
ETL Web Dashboard - Flask-based web UI for monitoring ETL pipeline
Fixed version with corrected HTML
"""

import sys
from pathlib import Path

# Add project to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from monitor_etl import ETLMonitor, ETLRun
except ImportError as e:
    print(f"❌ Error importing monitor_etl: {e}")
    sys.exit(1)

try:
    from flask import Flask, render_template_string, jsonify
except ImportError:
    print("⚠️  Flask not installed. Install with: pip install flask")
    sys.exit(1)

app = Flask(__name__)

# Global monitor
monitor = None

def init_monitor():
    """Initialize monitor"""
    global monitor
    try:
        monitor = ETLMonitor()
        monitor.parse_log()
        print("✅ Monitor initialized successfully")
        return True
    except Exception as e:
        print(f"⚠️  Error initializing monitor: {e}")
        monitor = None
        return False

# Modern HTML Dashboard
DASHBOARD_HTML = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KiotViet ETL Monitor</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { 
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e22ce 100%);
  min-height: 100vh; 
  padding: 30px 15px;
  color: #333;
}
.container { max-width: 1200px; margin: 0 auto; }
header { 
  color: white; 
  margin-bottom: 40px;
  text-align: center;
}
header h1 { 
  font-size: 2.5em; 
  margin-bottom: 8px;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(0,0,0,0.2);
}
header p { 
  font-size: 1em;
  opacity: 0.9;
  margin-bottom: 12px;
}
.status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255,255,255,0.95);
  padding: 15px 20px;
  border-radius: 10px;
  margin-bottom: 30px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
}
.status-info { font-size: 0.9em; color: #666; }
.status-time { font-weight: 600; color: #2a5298; font-size: 0.95em; }
.refresh-indicator {
  display: inline-block;
  width: 8px;
  height: 8px;
  background: #10b981;
  border-radius: 50%;
  margin-right: 6px;
  animation: pulse 2s infinite;
}
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

.latest-run {
  background: white;
  border-radius: 12px;
  padding: 25px;
  margin-bottom: 30px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.15);
  border-left: 5px solid #10b981;
}
.latest-run h2 {
  font-size: 1.1em;
  color: #666;
  margin-bottom: 15px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}
.latest-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}
.latest-item { display: flex; align-items: center; }
.latest-icon { font-size: 2em; margin-right: 12px; }
.latest-data { flex: 1; }
.latest-label { font-size: 0.75em; color: #999; text-transform: uppercase; margin-bottom: 4px; }
.latest-value { font-size: 1.5em; font-weight: 700; color: #1e3c72; }
.latest-unit { font-size: 0.5em; color: #aaa; margin-left: 3px; }

.progress-container { margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee; }
.progress-item { margin-bottom: 15px; }
.progress-label { display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 0.85em; }
.progress-label span:first-child { color: #666; font-weight: 600; }
.progress-label span:last-child { color: #2a5298; font-weight: 600; }
.progress-bar { background: #e5e7eb; height: 6px; border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #3b82f6, #10b981); border-radius: 3px; transition: width 0.3s ease; }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
  margin-bottom: 30px;
}
.stat-card {
  background: white;
  border-radius: 10px;
  padding: 18px;
  text-align: center;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  transition: transform 0.2s, box-shadow 0.2s;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,0.12); }
.stat-label { font-size: 0.75em; color: #999; text-transform: uppercase; margin-bottom: 8px; font-weight: 600; }
.stat-value { font-size: 2em; font-weight: 700; color: #2a5298; }
.stat-unit { font-size: 0.4em; color: #ccc; margin-left: 3px; }

.history-section {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.15);
}
.history-section h3 { font-size: 1.1em; color: #1e3c72; margin-bottom: 20px; font-weight: 600; }
table { width: 100%; border-collapse: collapse; font-size: 0.9em; }
table thead { background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%); border-bottom: 2px solid #d1d5db; }
table th { padding: 14px; text-align: left; font-weight: 600; color: #374151; letter-spacing: 0.3px; }
table td { padding: 14px; border-bottom: 1px solid #e5e7eb; }
table tbody tr:hover { background: #f9fafb; }
.status-badge { display: inline-flex; align-items: center; gap: 4px; padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 0.8em; }
.status-success { background: #d1fae5; color: #065f46; }
.status-failed { background: #fee2e2; color: #7f1d1d; }
.time-cell { font-family: monospace; font-size: 0.85em; color: #2a5298; }
.duration-cell { font-weight: 600; color: #10b981; }

footer { color: white; text-align: center; margin-top: 40px; font-size: 0.85em; opacity: 0.9; }

@media (max-width: 768px) {
  header h1 { font-size: 1.8em; }
  .latest-content { grid-template-columns: 1fr; }
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
</head>
<body>
<div class="container">
<header>
  <h1>📊 KiotViet ETL Monitor</h1>
  <p>Real-time pipeline performance dashboard</p>
</header>

<div class="status-bar">
  <div class="status-info">
    <span class="refresh-indicator"></span>
    <span>Status: Active</span>
  </div>
  <div class="status-time">Last update: <span id="rt">-</span></div>
</div>

<div class="latest-run">
  <h2>🚀 Latest Run</h2>
  <div class="latest-content">
    <div class="latest-item">
      <div class="latest-icon">⏰</div>
      <div class="latest-data">
        <div class="latest-label">Timestamp</div>
        <div class="latest-value" id="lt-time">-</div>
      </div>
    </div>
    <div class="latest-item">
      <div class="latest-icon">📦</div>
      <div class="latest-data">
        <div class="latest-label">Products</div>
        <div class="latest-value"><span id="lt-products">0</span><span class="latest-unit">items</span></div>
      </div>
    </div>
    <div class="latest-item">
      <div class="latest-icon">📋</div>
      <div class="latest-data">
        <div class="latest-label">Invoice Lines</div>
        <div class="latest-value"><span id="lt-invoices">0</span><span class="latest-unit">lines</span></div>
      </div>
    </div>
    <div class="latest-item">
      <div class="latest-icon">⏱️</div>
      <div class="latest-data">
        <div class="latest-label">Total Time</div>
        <div class="latest-value"><span id="lt-duration">0</span><span class="latest-unit">sec</span></div>
      </div>
    </div>
  </div>
  
  <div class="progress-container">
    <div class="progress-item">
      <div class="progress-label">
        <span>Invoice Sync</span>
        <span>~2.0s</span>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" id="inv-progress" style="width: 13%;"></div>
      </div>
    </div>
    <div class="progress-item">
      <div class="progress-label">
        <span>Product Export</span>
        <span>~6.0s</span>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" id="prod-progress" style="width: 40%;"></div>
      </div>
    </div>
  </div>
</div>

<div class="stats-grid">
  <div class="stat-card">
    <div class="stat-label">Today's Runs</div>
    <div class="stat-value" id="today-count">0</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Successful</div>
    <div class="stat-value" id="today-success">0</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Success Rate</div>
    <div class="stat-value"><span id="success-rate">0</span><span class="stat-unit">%</span></div>
  </div>
</div>

<div class="history-section">
  <h3>📈 Run History (Last 10)</h3>
  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>Status</th>
        <th>Timestamp</th>
        <th>Products</th>
        <th>Lines</th>
        <th>Duration</th>
      </tr>
    </thead>
    <tbody id="tb">
      <tr><td colspan="6" style="text-align:center;color:#999;padding:30px;">Loading...</td></tr>
    </tbody>
  </table>
</div>

<footer>
  <p>🔄 Auto-refresh every 10 seconds | Monitoring KiotViet ETL Pipeline</p>
</footer>
</div>

<script>
function refresh() {
  fetch('/api/data')
    .then(function(r) { return r.json(); })
    .then(function(d) {
      document.getElementById('rt').textContent = new Date().toLocaleTimeString();
      
      if (d.latest) {
        document.getElementById('lt-time').textContent = d.latest.timestamp || '-';
        document.getElementById('lt-products').textContent = d.latest.product_count || 0;
        document.getElementById('lt-invoices').textContent = d.latest.invoice_lines || 0;
        document.getElementById('lt-duration').textContent = d.latest.total_duration ? d.latest.total_duration.toFixed(1) : '0.0';
      }
      
      if (d.today) {
        document.getElementById('today-count').textContent = d.today.count;
        document.getElementById('today-success').textContent = d.today.successful;
      }
      
      if (d.stats) {
        document.getElementById('success-rate').textContent = d.stats.success_rate ? d.stats.success_rate.toFixed(1) : '0';
      }
      
      var h = '';
      if (d.last_10 && d.last_10.length > 0) {
        var reversed = d.last_10.slice().reverse();
        reversed.forEach(function(r, i) {
          var st = r.status === 'success' ? 'Success' : 'Failed';
          var sc = r.status === 'success' ? 'status-success' : 'status-failed';
          var dur = r.total_duration ? r.total_duration.toFixed(1) : '0.0';
          h += '<tr><td>' + (reversed.length - i) + '</td><td><span class="status-badge ' + sc + '">' + st + '</span></td><td class="time-cell">' + r.timestamp + '</td><td>' + r.product_count + '</td><td>' + r.invoice_lines + '</td><td class="duration-cell">' + dur + 's</td></tr>';
        });
      }
      document.getElementById('tb').innerHTML = h || '<tr><td colspan="6" style="text-align:center;color:#999;padding:20px;">No data</td></tr>';
    })
    .catch(function(e) { console.error('Refresh error:', e); });
}

window.addEventListener('load', function() {
  refresh();
  setInterval(refresh, 10000);
});
</script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/data')
def api_data():
    try:
        if monitor is None:
            return jsonify({"error": "Monitor not initialized"}), 500
        
        monitor.parse_log()
        
        latest = monitor.get_latest_run()
        today_runs = monitor.get_today_runs()
        stats = monitor.get_statistics()
        last_10 = monitor.get_last_n_runs(10)
        
        return jsonify({
            "latest": {
                "timestamp": latest.formatted_time if latest else "-",
                "product_count": latest.product_count if latest else 0,
                "invoice_lines": latest.invoice_lines if latest else 0,
                "total_duration": latest.total_duration if latest else 0,
            } if latest else {},
            "today": {
                "count": len(today_runs),
                "successful": len([r for r in today_runs if r.is_success]),
            },
            "stats": {
                "success_rate": stats.get("success_rate", 0),
            },
            "last_10": [
                {
                    "timestamp": r.formatted_time,
                    "status": r.status,
                    "product_count": r.product_count,
                    "invoice_lines": r.invoice_lines,
                    "total_duration": r.total_duration,
                }
                for r in last_10
            ],
        })
    except Exception as e:
        print(f"❌ API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*50)
    print("  KiotViet ETL Web Dashboard")
    print("="*50)
    
    if not init_monitor():
        print("❌ Failed to initialize monitor")
        sys.exit(1)
    
    print("\n🌐 Dashboard starting...")
    print("   http://localhost:5000")
    print("   http://192.168.1.99:5000 (local network)")
    print("\n💡 Remote access:")
    print("   ssh -L 5000:localhost:5000 hhaiviet@116.102.136.220")
    print("   Then: http://localhost:5000")
    print("\n" + "="*50)
    print("Press Ctrl+C to stop\n")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n✅ Dashboard stopped")
