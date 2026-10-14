"""Minimal mock of mihomo external-controller for testing (GET/PATCH /configs, DELETE /connections).
GET /configs mirrors the shape of mihomo executor.GetGeneral(): top-level ports + a nested tun object."""
import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
SECRET = sys.argv[2] if len(sys.argv) > 2 else ''
state = {'mode': 'rule', 'closed': 0, 'tun': False}
class H(BaseHTTPRequestHandler):
    def auth(self):
        if SECRET and self.headers.get('Authorization') != 'Bearer ' + SECRET:
            self.send_response(401); self.end_headers(); self.wfile.write(b'{"message":"Unauthorized"}'); return False
        return True
    def do_GET(self):
        if not self.auth(): return
        if self.path == '/configs':
            b = json.dumps({'port': 0, 'socks-port': 7891, 'redir-port': 0, 'tproxy-port': 0, 'mixed-port': 7890,
                            'tun': {'enable': state['tun'], 'device': 'Meta', 'stack': 'Mixed', 'dns-hijack': ['any:53'],
                                    'auto-route': True, 'auto-detect-interface': True, 'mtu': 9000,
                                    'route-address': [], 'file-descriptor': 0},
                            'tuic-server': {'enable': True, 'listen': '', 'port': 1234},
                            'allow-lan': False, 'bind-address': '*', 'mode': state['mode'], 'log-level': 'info',
                            'find-process-mode': 'strict', 'ipv6': True}).encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(b)
        else: self.send_response(404); self.end_headers()
    def do_PATCH(self):
        if not self.auth(): return
        n = int(self.headers.get('Content-Length', 0)); body = json.loads(self.rfile.read(n))
        assert self.headers.get('Content-Type','').startswith('application/json')
        if 'tun' in body: state['tun'] = bool(body['tun'].get('enable'))
        if 'mode' in body:
            if body['mode'] not in ('rule', 'global', 'direct'):
                self.send_response(400); self.end_headers(); return
            state['mode'] = body['mode']
        self.send_response(204); self.end_headers()
    def do_DELETE(self):
        if not self.auth(): return
        if self.path == '/connections':
            state['closed'] += 1; self.send_response(204); self.end_headers()
        else:
            self.send_response(404); self.end_headers()
    def log_message(self, *a): sys.stderr.write('mock: ' + (a[0] % a[1:]) + '\n')
HTTPServer(('127.0.0.1', int(sys.argv[1])), H).serve_forever()
