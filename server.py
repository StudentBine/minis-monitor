from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import time
import psutil

class Handler(BaseHTTPRequestHandler):
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
                data = {
                    "cpu": psutil.cpu_percent(interval=None),
                    "ram": psutil.virtual_memory().percent
                }

                self.wfile.write(f"data: {json.dumps(data)}\n\n".encode())
                self.wfile.flush()
                time.sleep(1)

server = HTTPServer(("0.0.0.0", 7000), Handler)
print("Running on http://0.0.0.0:7000")
server.serve_forever()