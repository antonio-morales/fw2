#!/usr/bin/env node
const net = require('net');
const crypto = require('crypto');

const HOST = '127.0.0.1';
const PORT = 80;
const ITERATIONS = Number(process.argv[2]) || 1000;
const TIMEOUT_MS = 2000;

const METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'PATCH', 'TRACE', 'CONNECT', 'FUZZ', ''];
const VERSIONS = ['HTTP/1.0', 'HTTP/1.1', 'HTTP/2.0', 'HTTP/9.9', 'http/1.1', '', 'HTTP/1.1\r\nX-Smuggle: 1'];
const HEADER_NAMES = ['Host', 'User-Agent', 'Accept', 'Cookie', 'Content-Length', 'Transfer-Encoding',
                     'X-Forwarded-For', 'Authorization', 'Range', 'Referer', 'Connection', 'Expect', 'Upgrade'];

function rnd(n) { return Math.floor(Math.random() * n); }
function pick(a) { return a[rnd(a.length)]; }

function randomBytes(len) {
  return crypto.randomBytes(len).toString('binary');
}

function randomString(len, alphabet) {
  const chars = alphabet || 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/?&=._-%';
  let s = '';
  for (let i = 0; i < len; i++) s += chars[rnd(chars.length)];
  return s;
}

function mutate(s) {
  const ops = [
    () => s + randomString(rnd(32)),
    () => randomString(rnd(32)) + s,
    () => s.slice(0, rnd(s.length)) + randomBytes(rnd(8)) + s.slice(rnd(s.length)),
    () => s.repeat(1 + rnd(50)),
    () => s.replace(/[a-z]/g, c => rnd(2) ? c.toUpperCase() : c),
    () => s + '\x00' + randomString(rnd(16)),
    () => s + '\r\n' + randomString(rnd(16)) + ': ' + randomString(rnd(16)),
  ];
  return pick(ops)();
}

function buildRequest() {
  const method = pick(METHODS);
  const pathLen = rnd(300);
  let path = '/' + randomString(pathLen);
  if (rnd(4) === 0) path = mutate(path);
  if (rnd(6) === 0) path = '/' + '../'.repeat(rnd(20)) + randomString(rnd(20));

  const version = pick(VERSIONS);
  const lines = [`${method} ${path} ${version}`];

  const headerCount = rnd(15);
  for (let i = 0; i < headerCount; i++) {
    let name = pick(HEADER_NAMES);
    if (rnd(5) === 0) name = randomString(rnd(30), 'abcdefghijklmnopqrstuvwxyz-');
    let value = randomString(rnd(200));
    if (rnd(4) === 0) value = mutate(value);
    lines.push(`${name}: ${value}`);
  }

  if (rnd(3) === 0) lines.push(`Host: ${randomString(rnd(50))}`);

  let body = '';
  if (['POST', 'PUT', 'PATCH'].includes(method) || rnd(5) === 0) {
    body = randomBytes(rnd(4096));
    if (rnd(3) === 0) {
      lines.push(`Content-Length: ${body.length + (rnd(5) === 0 ? rnd(1000) - 500 : 0)}`);
    }
    if (rnd(5) === 0) lines.push('Transfer-Encoding: chunked');
  }

  const separator = rnd(10) === 0 ? '\n' : '\r\n';
  return lines.join(separator) + separator + separator + body;
}

function sendRequest(payload, id) {
  return new Promise((resolve) => {
    const start = Date.now();
    const socket = net.createConnection(PORT, HOST);
    let received = Buffer.alloc(0);
    let done = false;

    const finish = (status, extra) => {
      if (done) return;
      done = true;
      socket.destroy();
      resolve({ id, status, elapsed: Date.now() - start, size: received.length, extra });
    };

    socket.setTimeout(TIMEOUT_MS);
    socket.on('connect', () => socket.write(payload, 'binary'));
    socket.on('data', (chunk) => {
      received = Buffer.concat([received, chunk]);
      if (received.length > 65536) finish('ok');
    });
    socket.on('end', () => finish('ok'));
    socket.on('timeout', () => finish('timeout'));
    socket.on('error', (err) => finish('error', err.code || err.message));
  });
}

function interesting(res) {
  if (res.status === 'timeout') return true;
  if (res.status === 'error' && res.extra !== 'ECONNRESET' && res.extra !== 'ECONNREFUSED') return true;
  if (res.elapsed > 1000) return true;
  if (res.size === 0 && res.status === 'ok') return true;
  return false;
}

async function main() {
  console.log(`Fuzzing http://${HOST}:${PORT} for ${ITERATIONS} iterations`);
  let oks = 0, errs = 0, timeouts = 0, flagged = 0;
  for (let i = 0; i < ITERATIONS; i++) {
    const payload = buildRequest();
    const res = await sendRequest(payload, i);
    if (res.status === 'ok') oks++;
    else if (res.status === 'timeout') timeouts++;
    else errs++;

    if (interesting(res)) {
      flagged++;
      console.log(`[!] #${i} status=${res.status} extra=${res.extra || ''} size=${res.size} time=${res.elapsed}ms`);
      console.log('--- payload ---');
      console.log(payload.slice(0, 500).replace(/[^\x20-\x7e\r\n]/g, '.'));
      console.log('---------------');
    }

    if ((i + 1) % 100 === 0) {
      console.log(`[${i + 1}/${ITERATIONS}] ok=${oks} err=${errs} timeout=${timeouts} flagged=${flagged}`);
    }
  }
  console.log(`Done. ok=${oks} err=${errs} timeout=${timeouts} flagged=${flagged}`);
}

main().catch(e => { console.error(e); process.exit(1); });
