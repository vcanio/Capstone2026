"""Puente local con contraseña para un túnel HTTPS temporal de Cloudflare."""
import base64
import hmac
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import secrets

PORT = 18095
TARGET = 8095
PASSWORD = secrets.token_urlsafe(18)


class Proxy(BaseHTTPRequestHandler):
    def authenticate(self):
        expected = 'Basic ' + base64.b64encode(('vision:' + PASSWORD).encode()).decode()
        if hmac.compare_digest(self.headers.get('Authorization', ''), expected):
            return True
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="Walmart Vision", charset="UTF-8"')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', '0')
        self.end_headers()
        return False

    def forward(self):
        if not self.authenticate():
            return
        if self.command == 'POST':
            origin = self.headers.get('Origin', '')
            host = self.headers.get('Host', '')
            if origin != 'https://' + host:
                self.send_error(403)
                return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length < 0 or length > 15 * 1024 * 1024:
                self.send_error(413)
                return
            body = self.rfile.read(length) if length else None
            target = http.client.HTTPConnection('127.0.0.1', TARGET, timeout=330)
            headers = {'Host': f'127.0.0.1:{TARGET}', 'Origin': f'http://127.0.0.1:{TARGET}'}
            if body is not None:
                headers['Content-Type'] = self.headers.get('Content-Type', 'application/octet-stream')
            target.request(self.command, self.path, body=body, headers=headers)
            response = target.getresponse()
            data = response.read()
            self.send_response(response.status)
            self.send_header('Content-Type', response.getheader('Content-Type', 'application/octet-stream'))
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(data)
            target.close()
        except (OSError, ValueError, http.client.HTTPException):
            self.send_error(502, 'Aplicacion local no disponible')

    do_GET = forward
    do_POST = forward

    def log_message(self, *_):
        pass


if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', PORT), Proxy)
    print('Usuario: vision', flush=True)
    print('Contraseña: ' + PASSWORD, flush=True)
    print(f'Puente local activo en 127.0.0.1:{PORT}', flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
