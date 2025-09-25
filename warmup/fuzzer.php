#!/usr/bin/env php
<?php

declare(strict_types=1);

final class Fuzzer
{
    private string $host;
    private int $port;
    private int $count;
    private int $timeoutSec;

    public function __construct(string $host = '127.0.0.1', int $port = 80, int $count = 100, int $timeoutSec = 2)
    {
        $this->host = $host;
        $this->port = $port;
        $this->count = $count;
        $this->timeoutSec = $timeoutSec;
    }

    public function run(): int
    {
        $ok = 0;
        for ($i = 1; $i <= $this->count; $i++) {
            $req = $this->makeReq();
            $start = microtime(true);
            $resp = $this->send($req);
            $durMs = (int) ((microtime(true) - $start) * 1000);

            $status = $this->firstLine($resp);
            $sent = strlen($req);
            $rcv = strlen($resp);

            $ok += $resp === '' ? 0 : 1;

            fwrite(STDOUT, sprintf("[%d/%d] %s | sent=%dB recv=%dB time=%dms\n", $i, $this->count, $status, $sent, $rcv, $durMs));
        }

        fwrite(STDOUT, sprintf("Done. Successful responses: %d/%d\n", $ok, $this->count));
        return 0;
    }

    private function send(string $req): string
    {
        $errno = 0;
        $errstr = '';
        $fp = @stream_socket_client(
            sprintf('tcp://%s:%d', $this->host, $this->port),
            $errno,
            $errstr,
            $this->timeoutSec
        );

        if ($fp === false) {
            fwrite(STDERR, sprintf("connect failed: [%d] %s\n", $errno, $errstr));
            return '';
        }

        stream_set_timeout($fp, $this->timeoutSec);

        $written = @fwrite($fp, $req);
        if ($written === false) {
            fclose($fp);
            fwrite(STDERR, "write failed\n");
            return '';
        }

        $resp = @stream_get_contents($fp);
        fclose($fp);
        if ($resp === false) {
            fwrite(STDERR, "read failed\n");
            return '';
        }
        return $resp;
    }

    private function makeReq(): string
    {
        $methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', 'TRACE'];
        $method = $methods[random_int(0, count($methods) - 1)];

        $path = $this->randPath();
        $headers = [
            'Host' => $this->host,
            'User-Agent' => 'fw2-fuzzer/1.0',
            'Accept' => '*/*',
            'Connection' => 'close',
            $this->randHeaderName() => $this->randAscii(4, 16),
        ];

        $body = '';
        if (in_array($method, ['POST', 'PUT', 'PATCH', 'DELETE'], true) && random_int(0, 1) === 1) {
            // Mix of ASCII and binary
            $len = random_int(0, 512);
            $body = random_int(0, 1) === 1 ? $this->randAscii(0, $len) : random_bytes($len);
            $headers['Content-Type'] = random_int(0, 1) === 1 ? 'application/octet-stream' : 'text/plain';
            $headers['Content-Length'] = (string) strlen($body);
        }

        // Sometimes add malformed or odd headers
        if (random_int(0, 3) === 0) {
            $headers[$this->randHeaderName()] = '';
        }

        $req = sprintf("%s %s HTTP/1.1\r\n", $method, $path);
        foreach ($headers as $k => $v) {
            $req .= sprintf("%s: %s\r\n", $k, $v);
        }
        $req .= "\r\n";
        $req .= $body;

        // Sometimes send extra CRLF to test tolerance
        if (random_int(0, 4) === 0) {
            $req .= "\r\n\r\n";
        }

        return $req;
    }

    private function randPath(): string
    {
        $segCount = random_int(0, 4);
        $segs = [];
        for ($i = 0; $i < $segCount; $i++) {
            $segs[] = rawurlencode($this->randAscii(1, random_int(1, 10)));
        }
        $q = '';
        if (random_int(0, 2) === 0) {
            $q = '?' . http_build_query([
                $this->randAscii(1, 5) => $this->randAscii(0, 8),
                $this->randAscii(1, 5) => $this->randAscii(0, 8),
            ]);
        }
        return '/' . implode('/', $segs) . $q;
    }

    private function randHeaderName(): string
    {
        $base = $this->randAscii(3, 10);
        return 'X-' . str_replace(' ', '-', ucwords(str_replace(['-', '_'], ' ', $base)));
    }

    private function randAscii(int $min, int $max): string
    {
        $len = random_int($min, $max);
        $chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~!@#$%^&*()[]{}:;,. ';
        $out = '';
        for ($i = 0; $i < $len; $i++) {
            $out .= $chars[random_int(0, strlen($chars) - 1)];
        }
        return $out;
    }

    private function firstLine(string $resp): string
    {
        if ($resp === '') {
            return 'no-response';
        }
        $pos = strpos($resp, "\r\n");
        if ($pos === false) {
            return substr($resp, 0, 60);
        }
        return substr($resp, 0, $pos);
    }
}

function parseArgs(array $argv): array
{
    $host = '127.0.0.1';
    $port = 80;
    $count = 100;
    $timeout = 2;

    foreach ($argv as $arg) {
        if (str_starts_with($arg, '--host=')) {
            $host = substr($arg, 7);
        } elseif (str_starts_with($arg, '--port=')) {
            $port = (int) substr($arg, 7);
        } elseif (str_starts_with($arg, '--count=')) {
            $count = max(1, (int) substr($arg, 8));
        } elseif (str_starts_with($arg, '--timeout=')) {
            $timeout = max(1, (int) substr($arg, 10));
        } elseif ($arg === '--help' || $arg === '-h') {
            fwrite(STDOUT, "\nUsage: php warmup/fuzzer.php [--host=127.0.0.1] [--port=80] [--count=100] [--timeout=2]\n\n");
            exit(0);
        }
    }

    return [$host, $port, $count, $timeout];
}

if (PHP_SAPI !== 'cli') {
    fwrite(STDERR, "Run from CLI.\n");
    exit(1);
}

[$host, $port, $count, $timeout] = parseArgs($argv);

$fuzzer = new Fuzzer(host: $host, port: $port, count: $count, timeoutSec: $timeout);
exit($fuzzer->run());
