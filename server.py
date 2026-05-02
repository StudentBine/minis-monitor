from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import time
import psutil
from collections import deque

class MetricsBuffer:
    def __init__(self, max_size=60):
        self.max_size = max_size
        self.cpu_history = deque(maxlen=max_size)
        self.ram_history = deque(maxlen=max_size)
        self.timestamp = 0

metrics_buffer = MetricsBuffer()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress log messages

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open("index.html", "rb") as f:
                self.wfile.write(f.read())

        elif self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            while True:
                try:
                    cpu_percent = psutil.cpu_percent(interval=1)
                    cpu_per_core = psutil.cpu_percent(interval=None, percpu=True)
                    vm = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')
                    net = psutil.net_io_counters()
                    
                    # Store history
                    metrics_buffer.cpu_history.append(cpu_percent)
                    metrics_buffer.ram_history.append(vm.percent)
                    metrics_buffer.timestamp += 1

                    # Get top processes
                    processes = []
                    try:
                        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                            try:
                                pinfo = proc.info
                                if pinfo['cpu_percent'] is not None and pinfo['memory_percent'] is not None:
                                    processes.append(pinfo)
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pass
                    except:
                        pass
                    
                    # Sort by CPU usage and take top 5
                    processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
                    top_processes = [{'name': p['name'], 'cpu': round(p['cpu_percent'], 1), 'memory': round(p['memory_percent'], 1)} 
                                   for p in processes[:5]]

                    data = {
                        "cpu": round(cpu_percent, 1),
                        "cpu_cores": len(cpu_per_core),
                        "cpu_per_core": [round(c, 1) for c in cpu_per_core],
                        "ram": round(vm.percent, 1),
                        "ram_used": round(vm.used / (1024**3), 2),  # GB
                        "ram_total": round(vm.total / (1024**3), 2),  # GB
                        "ram_available": round(vm.available / (1024**3), 2),  # GB
                        "disk": round(disk.percent, 1),
                        "disk_used": round(disk.used / (1024**3), 2),  # GB
                        "disk_total": round(disk.total / (1024**3), 2),  # GB
                        "disk_free": round(disk.free / (1024**3), 2),  # GB
                        "net_sent": round(net.bytes_sent / (1024**3), 2),  # GB
                        "net_recv": round(net.bytes_recv / (1024**3), 2),  # GB
                        "cpu_count": psutil.cpu_count(),
                        "cpu_freq": round(psutil.cpu_freq().current, 1) if psutil.cpu_freq() else 0,
                        "top_processes": top_processes,
                        "history": {
                            "cpu": list(metrics_buffer.cpu_history),
                            "ram": list(metrics_buffer.ram_history)
                        }
                    }

                    self.wfile.write(f"data: {json.dumps(data)}\n\n".encode())
                    self.wfile.flush()
                    time.sleep(1)
                except Exception as e:
                    print(f"Error: {e}")
                    time.sleep(1)

server = HTTPServer(("0.0.0.0", 7000), Handler)
print("Running on http://0.0.0.0:7000")
server.serve_forever()