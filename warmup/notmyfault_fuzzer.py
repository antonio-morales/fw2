#!/usr/bin/env python3
import socket
import time
import random
import string

class HTTPFuzzer:
    def __init__(self, host='localhost', port=80, timeout=5):
        self.host = host
        self.port = port
        self.timeout = timeout

    def send_request(self, request_data):
        """Send HTTP request and return response"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))

            sock.send(request_data.encode('utf-8', errors='ignore'))

            response = b""
            try:
                while True:
                    data = sock.recv(4096)
                    if not data:
                        break
                    response += data
            except socket.timeout:
                pass

            sock.close()
            return response.decode('utf-8', errors='ignore')

        except Exception as e:
            return f"Error: {str(e)}"

    def generate_malformed_requests(self):
        """Generate various malformed HTTP requests"""
        requests = []

        # Valid baseline request
        valid_request = "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
        requests.append(("Valid Request", valid_request))

        # Request line fuzzing
        request_line_variations = [
            "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n",
            "GET / HTTP/999.999\r\nHost: localhost\r\n\r\n",
            "GET / INVALID/1.1\r\nHost: localhost\r\n\r\n",
            "GET\r\nHost: localhost\r\n\r\n",
            "GET /\r\nHost: localhost\r\n\r\n",
            "INVALID / HTTP/1.1\r\nHost: localhost\r\n\r\n",
            "GET /../../../etc/passwd HTTP/1.1\r\nHost: localhost\r\n\r\n",
            "GET " + "A" * 10000 + " HTTP/1.1\r\nHost: localhost\r\n\r\n",
            "GET / HTTP/1.1" + "A" * 1000 + "\r\nHost: localhost\r\n\r\n",
            "\r\nGET / HTTP/1.1\r\nHost: localhost\r\n\r\n",
            "GET / HTTP/1.1\n\nHost: localhost\n\n",
            "get / http/1.1\r\nhost: localhost\r\n\r\n",
        ]

        for i, req in enumerate(request_line_variations):
            requests.append((f"Request Line Variation {i+1}", req))

        # Header fuzzing
        header_variations = [
            "GET / HTTP/1.1\r\nHost: localhost\r\nContent-Length: -1\r\n\r\n",
            "GET / HTTP/1.1\r\nHost: localhost\r\nContent-Length: 999999999\r\n\r\n",
            "GET / HTTP/1.1\r\nHost: localhost\r\nTransfer-Encoding: chunked\r\nContent-Length: 10\r\n\r\n",
            "GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\nConnection: keep-alive\r\n\r\n",
            "GET / HTTP/1.1\r\nHost: localhost\r\n" + "X-Custom: " + "A" * 10000 + "\r\n\r\n",
            "GET / HTTP/1.1\r\nHost: localhost\r\n" + "A" * 1000 + ": value\r\n\r\n",
            "GET / HTTP/1.1\r\nHost: localhost\r\nHeader-Without-Value:\r\n\r\n",
            "GET / HTTP/1.1\r\nHost: localhost\r\nNo-Colon-Header\r\n\r\n",
            "GET / HTTP/1.1\r\nHost: localhost\r\n\x00\x01\x02: binary\r\n\r\n",
            "GET / HTTP/1.1\r\nHost: localhost\r\nUser-Agent: \r\n\r\n",
            "GET / HTTP/1.1\r\nHost:\r\n\r\n",
            "GET / HTTP/1.1\r\n\r\n",
        ]

        for i, req in enumerate(header_variations):
            requests.append((f"Header Variation {i+1}", req))

        # Special character and encoding variations
        special_variations = [
            "GET / HTTP/1.1\r\nHost: localhost\r\nTest: \x80\x81\x82\r\n\r\n",
            "GET / HTTP/1.1\r\nHost: localhost\r\nTest: %00%01%02\r\n\r\n",
            "GET /%2e%2e/%2e%2e/etc/passwd HTTP/1.1\r\nHost: localhost\r\n\r\n",
            "GET / HTTP/1.1\r\nHost: localhost\r\nTest: <script>alert(1)</script>\r\n\r\n",
            "GET / HTTP/1.1\r\nHost: localhost\r\nTest: ' OR 1=1--\r\n\r\n",
            "GET / HTTP/1.1\r\nHost: localhost\r\nTest: \"; rm -rf /\r\n\r\n",
        ]

        for i, req in enumerate(special_variations):
            requests.append((f"Special Character Variation {i+1}", req))

        # Malformed structure variations
        structure_variations = [
            "GET / HTTP/1.1\r\nHost: localhost\r\n",  # Missing final CRLF
            "GET / HTTP/1.1\nHost: localhost\n\n",    # Wrong line endings
            "GET / HTTP/1.1Host: localhost\r\n\r\n",  # Missing CRLF after request line
            "\x00\x00GET / HTTP/1.1\r\nHost: localhost\r\n\r\n",  # Binary prefix
            "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n" + "A" * 1000,  # Extra data
            "",  # Empty request
            "\r\n\r\n",  # Only CRLF
            "GET / HTTP/1.1" + "\r\n" * 1000 + "Host: localhost\r\n\r\n",  # Many empty lines
        ]

        for i, req in enumerate(structure_variations):
            requests.append((f"Structure Variation {i+1}", req))

        return requests

    def run_fuzzing(self, delay=0.1):
        """Run the fuzzing campaign"""
        print(f"Starting HTTP fuzzing against {self.host}:{self.port}")
        print("=" * 60)

        requests = self.generate_malformed_requests()

        for test_name, request in requests:
            print(f"\n[{test_name}]")
            print(f"Request: {repr(request[:100])}{'...' if len(request) > 100 else ''}")

            response = self.send_request(request)

            if response.startswith("Error:"):
                print(f"Connection Error: {response}")
            else:
                status_line = response.split('\n')[0] if response else "No response"
                print(f"Response: {status_line}")

                if "500" in status_line or "400" in status_line:
                    print("⚠️  Potential issue detected!")
                elif "200" in status_line:
                    print("✓ Normal response")
                else:
                    print("? Unexpected response")

            time.sleep(delay)

        print("\n" + "=" * 60)
        print("Fuzzing campaign completed!")

def main():
    print("HTTP Fuzzer - Testing localhost:80")
    print("This tool sends malformed HTTP requests for security testing")
    print("Make sure you have permission to test the target!")

    fuzzer = HTTPFuzzer()

    try:
        fuzzer.run_fuzzing()
    except KeyboardInterrupt:
        print("\nFuzzing interrupted by user")
    except Exception as e:
        print(f"Fuzzing failed: {e}")

if __name__ == "__main__":
    main()
