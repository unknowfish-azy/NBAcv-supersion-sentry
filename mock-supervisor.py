from http.server import BaseHTTPRequestHandler, HTTPServer
import json
class H(BaseHTTPRequestHandler):
    def do_POST(self):
        n=int(self.headers.get('content-length','0')); body=self.rfile.read(n).decode()
        status='suspicious' if 'frame-002' in body else 'pass'
        payload={'choices':[{'message':{'content':json.dumps({'status':status,'reason':'mock evidence','confidence':0.91})}}]}
        out=json.dumps(payload).encode(); self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(out))); self.end_headers(); self.wfile.write(out)
HTTPServer(('127.0.0.1',8765),H).serve_forever()
