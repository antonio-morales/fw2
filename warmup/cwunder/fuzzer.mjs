#!/usr/bin/env node

// Simple network fuzzer - sends weird data to port 80
import { createConnection } from 'node:net';
import { randomBytes } from 'node:crypto';

const TARGET = { host: 'localhost', port: 80 };

// Generate random weird data
function generateWeirdData() {
    const patterns = [
        randomBytes(Math.floor(Math.random() * 1000)),           // Random binary
        Buffer.from('GET ' + 'A'.repeat(10000) + ' HTTP/1.1'),   // Huge request
        Buffer.from('GET /\x00\x01\x02 HTTP/1.1'),              // Null bytes
        Buffer.from('%x'.repeat(500)),                          // Format strings
        Buffer.from('POST / HTTP/1.1\r\nContent-Length: -1'),   // Invalid headers
    ];

    return patterns[Math.floor(Math.random() * patterns.length)];
}

// Send fuzzing payload
function fuzzTarget() {
    const socket = createConnection(TARGET);

    socket.on('connect', () => {
        const payload = generateWeirdData();
        console.log(`Sending ${payload.length} bytes of weird data...`);
        socket.write(payload);
        socket.end();
    });

    socket.on('error', (err) => console.log('Error:', err.message));
}

// Start fuzzing (send 100 requests)
for (let i = 0; i < 100; i++) {
    setTimeout(() => fuzzTarget(), i * 100);
}
