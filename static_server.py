from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

port = int(os.environ.get('PORT', 8080))
print(f"Starting server on port {port}")
httpd = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
httpd.serve_forever()