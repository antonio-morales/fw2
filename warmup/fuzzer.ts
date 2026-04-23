import { createConnection } from 'node:net'

const METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'FOO', '']
const VERSIONS = ['HTTP/1.0', 'HTTP/1.1', 'HTTP/9.9', '']
const HEADERS = ['Host', 'User-Agent', 'Cookie', 'Content-Length', 'X-Forwarded-For']

function pick<T> (arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)]!
}

function randStr (max: number): string {
  const n = Math.floor(Math.random() * max)
  let s = ''
  for (let i = 0; i < n; i++) s += String.fromCharCode(32 + Math.floor(Math.random() * 95))
  return s
}

function makeRequest (): string {
  let headers = ''
  for (let i = Math.floor(Math.random() * 6); i > 0; i--) {
    headers += `${pick(HEADERS)}: ${randStr(80)}\r\n`
  }
  const body = Math.random() < 0.3 ? randStr(500) : ''
  return `${pick(METHODS)} /${randStr(40)} ${pick(VERSIONS)}\r\n${headers}\r\n${body}`
}

function send (req: string): Promise<string> {
  return new Promise(resolve => {
    const sock = createConnection({ host: '127.0.0.1', port: 80 })
    sock.setTimeout(2000)
    sock.once('connect', () => sock.write(req))
    sock.once('data', d => {
      sock.destroy()
      resolve(d.toString('latin1').split(' ')[1] ?? 'unknown')
    })
    sock.once('timeout', () => { sock.destroy(); resolve('timeout') })
    sock.once('error', (err: Error & { code?: string }) => resolve(err.code ?? 'error'))
  })
}

async function main (): Promise<void> {
  const n = Number(process.argv[2] ?? 200)
  const stats = new Map<string, number>()
  for (let i = 0; i < n; i++) {
    const out = await send(makeRequest())
    stats.set(out, (stats.get(out) ?? 0) + 1)
  }
  console.log(Object.fromEntries(stats))
}

main()
