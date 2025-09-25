#!/usr/bin/env python3
"""
HTTP Fuzzer for localhost:80
Tests various HTTP methods with malformed payloads to identify potential crashes
"""

import socket
import random
import time
import string
import threading
from urllib.parse import quote

class HTTPFuzzer:
    def __init__(self, host='localhost', port=80, timeout=5):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.methods = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'TRACE', 'PATCH']
        self.crash_count = 0
        self.request_count = 0
        
    def generate_random_string(self, length):
        """Generate random string of specified length"""
        return ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=length))
    
    def generate_malformed_payloads(self):
        """Generate various malformed payloads"""
        payloads = [
            # Buffer overflow attempts
            'A' * 1000,
            'A' * 5000,
            'A' * 10000,
            
            # Format string attacks
            '%s%s%s%s%s%s%s%s%s%s',
            '%x%x%x%x%x%x%x%x%x%x',
            '%n%n%n%n%n%n%n%n%n%n',
            
            # SQL injection attempts
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "1' UNION SELECT * FROM users--",
            
            # XSS attempts
            '<script>alert("XSS")</script>',
            '<img src=x onerror=alert("XSS")>',
            
            # Path traversal
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\drivers\\etc\\hosts',
            
            # Command injection
            '; cat /etc/passwd',
            '| whoami',
            '`id`',
            
            # NULL bytes and control characters
            '\x00\x01\x02\x03\x04\x05',
            '\n\r\t\b\f',
            
            # Unicode and encoding issues
            '\u0000\u0001\u0002',
            '%00%01%02%03',
            
            # Random binary data
            bytes(random.getrandbits(8) for _ in range(100)).decode('latin-1'),
            
            # Very long strings
            self.generate_random_string(2000),
        ]
        return payloads
    
    def generate_malformed_headers(self):
        """Generate malformed HTTP headers"""
        headers = [
            'Content-Length: -1',
            'Content-Length: 999999999999999999999',
            'Transfer-Encoding: chunked\r\nTransfer-Encoding: identity',
            'Host: ' + 'A' * 1000,
            'User-Agent: ' + 'X' * 5000,
            'Authorization: Basic ' + 'A' * 10000,
            'Cookie: ' + 'session=' + 'X' * 8000,
            'X-Forwarded-For: ' + '127.0.0.1,' * 1000,
            'Content-Type: application/json\x00\x01\x02',
            'Accept: */*\n\rMalicious: Header',
        ]
        return headers
    
    def create_http_request(self, method, path, payload=None, headers=None):
        """Create HTTP request string"""
        if headers is None:
            headers = []
        
        request = f"{method} {path} HTTP/1.1\r\n"
        request += f"Host: {self.host}\r\n"
        
        # Add custom headers
        for header in headers:
            request += f"{header}\r\n"
        
        # Add payload for POST/PUT methods
        if payload and method in ['POST', 'PUT', 'PATCH']:
            request += f"Content-Length: {len(payload)}\r\n"
            request += "Content-Type: application/x-www-form-urlencoded\r\n"
            request += "\r\n"
            request += payload
        else:
            request += "\r\n"
        
        return request
    
    def send_request(self, request_data):
        """Send HTTP request and handle response"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
            
            sock.send(request_data.encode('latin-1'))
            
            response = sock.recv(4096)
            sock.close()
            
            self.request_count += 1
            return response.decode('latin-1', errors='ignore')
            
        except socket.error as e:
            self.crash_count += 1
            print(f"[!] Connection error (potential crash): {e}")
            return None
        except Exception as e:
            print(f"[!] Unexpected error: {e}")
            return None
    
    def fuzz_paths(self):
        """Fuzz different URL paths"""
        paths = [
            '/',
            '/index.html',
            '/admin',
            '/login',
            '/config',
            '/' + 'A' * 1000,
            '/../../../etc/passwd',
            '/?' + 'param=' + 'X' * 5000,
            '/\x00\x01\x02',
            '/' + quote('../' * 100),
        ]
        return paths
    
    def run_fuzzing_campaign(self, iterations=100):
        """Run comprehensive fuzzing campaign"""
        print(f"[+] Starting HTTP fuzzer against {self.host}:{self.port}")
        print(f"[+] Running {iterations} iterations...")
        
        payloads = self.generate_malformed_payloads()
        malformed_headers = self.generate_malformed_headers()
        paths = self.fuzz_paths()
        
        for i in range(iterations):
            try:
                # Random method selection
                method = random.choice(self.methods)
                path = random.choice(paths)
                
                # Random payload selection for POST/PUT
                payload = None
                if method in ['POST', 'PUT', 'PATCH']:
                    payload = random.choice(payloads)
                
                # Random header selection
                headers = []
                if random.random() < 0.3:  # 30% chance of malformed headers
                    headers = [random.choice(malformed_headers)]
                
                # Create and send request
                request = self.create_http_request(method, path, payload, headers)
                
                print(f"[{i+1}/{iterations}] Testing {method} {path[:50]}...")
                
                response = self.send_request(request)
                
                if response:
                    # Check for error responses that might indicate issues
                    if '500' in response or 'Internal Server Error' in response:
                        print(f"[!] Server error detected: {response[:200]}")
                    elif '400' in response:
                        print(f"[*] Bad request: {response[:100]}")
                
                # Small delay to avoid overwhelming the server
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\n[!] Fuzzing interrupted by user")
                break
            except Exception as e:
                print(f"[!] Fuzzing error: {e}")
        
        print(f"\n[+] Fuzzing completed!")
        print(f"[+] Total requests sent: {self.request_count}")
        print(f"[+] Connection errors (potential crashes): {self.crash_count}")

def main():
    print("HTTP Fuzzer for localhost:80")
    print("=" * 40)
    
    fuzzer = HTTPFuzzer()
    
    # Check if port 80 is accessible
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 80))
        sock.close()
        
        if result != 0:
            print("[!] Warning: Cannot connect to localhost:80")
            print("[!] Make sure a web server is running on port 80")
            return
        else:
            print("[+] Connection to localhost:80 successful")
            
    except Exception as e:
        print(f"[!] Error checking connection: {e}")
        return
    
    try:
        iterations = int(input("Enter number of fuzzing iterations (default 100): ") or "100")
    except ValueError:
        iterations = 100
    
    fuzzer.run_fuzzing_campaign(iterations)

if __name__ == "__main__":
    main()