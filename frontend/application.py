import http.server
import os
import socketserver

PORT = 8000

handler = http.server.SimpleHTTPRequestHandler
os.chdir("static")
with socketserver.TCPServer(("", PORT), handler) as httpd:
    print("Server started at localhost:" + str(PORT))
    httpd.serve_forever()
