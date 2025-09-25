#!/usr/bin/env python3

import http.server
import socketserver


class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        message = f"""
        <html>
            <head><title>Under construction</title></head>
            <body>
                <p>Hello world</p>
            </body>
        </html>
        """
        self.wfile.write(message.encode("utf-8"))


if __name__ == "__main__":
    PORT = 80
    with socketserver.TCPServer(("", PORT), SimpleHTTPRequestHandler) as httpd:
        print(f"Serving at port {PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
