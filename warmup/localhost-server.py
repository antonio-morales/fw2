#!/usr/bin/env python3

import http.server
import socketserver

PORT = 8080  # You can use 8000 or 8080 if 80 requires admin privileges

Handler = http.server.SimpleHTTPRequestHandler

def start_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

def main():
    start_server()

if __name__ == "__main__":
    main()
