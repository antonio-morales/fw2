import { randomBytes } from 'node:crypto'
import { connect } from 'node:tcp'

const methods = [
    'GET',
    'HEAD',
    'DELETE',
    'POST',
    'PUT',
    'OPTIONS',
]

const selectRandom = (list) => list[Math.floor(Math.random() * list.length)]

while (true) {
    const method = selectRandom(methods) + (
        Math.random() < 0.1 ? randomBytes(6).toString() : ''
    )
    const url = (Math.random() < 0.1 ? '/' : '') + randomBytes(Math.floor(Math.random() * 1024))
    const body = randomBytes(Math.floor(Math.random() * 1024))
    const conn = connect({
        host: 'localhost',
        port: 80,
    })

    const headers = []
    const h = Math.floor(Math.random() * 16)
    for (let i = 0; i < h; i++) {
        headers.push(randomBytes(6).toString('hex') + ': ' + randomBytes(16).toString('base64'))
    }
    conn.write(`${method} ${url} HTTP/1.1\r\n${headers.join('\r\n')}\r\n\r\n${body}\r\n`)
}