import * as RRTypes from '../index.js'
import RR from '../rr.js'

const ITERATIONS = Number.parseInt(process.env.FUZZ_ITERATIONS ?? '100', 10)
const SEED = Number.parseInt(process.env.FUZZ_SEED ?? '1337', 10)

function makeRng(seed) {
  let state = seed >>> 0
  return () => {
    state = (1664525 * state + 1013904223) >>> 0
    return state / 0x100000000
  }
}

function randInt(rng, min, max) {
  return Math.floor(rng() * (max - min + 1)) + min
}

function pick(rng, values) {
  return values[randInt(rng, 0, values.length - 1)]
}

function randomAscii(rng, min = 0, max = 32) {
  const len = randInt(rng, min, max)
  let out = ''
  for (let i = 0; i < len; i++) out += String.fromCharCode(randInt(rng, 32, 126))
  return out
}

function randomDomain(rng, fqdn = true) {
  const labels = randInt(rng, 1, 4)
  const parts = []
  for (let i = 0; i < labels; i++) {
    const len = randInt(rng, 1, 10)
    let label = ''
    for (let j = 0; j < len; j++) {
      label += pick(rng, 'abcdefghijklmnopqrstuvwxyz0123456789-'.split(''))
    }
    parts.push(label.replace(/^-+|-+$/g, 'a'))
  }
  const host = parts.join('.')
  return fqdn ? `${host}.` : host
}

function mutateString(rng, input = '') {
  const s = String(input)
  const variants = [
    '',
    randomAscii(rng, 1, 48),
    `${s}${randomAscii(rng, 1, 8)}`,
    randomDomain(rng, true),
    randomDomain(rng, false),
    `"${randomAscii(rng, 1, 16)}"`,
    '\\000\\001\\377',
    ':;\\\n\t',
  ]
  return pick(rng, variants)
}

function mutateNumber(rng, input = 0) {
  const n = Number(input)
  const variants = [
    -1,
    0,
    1,
    Number.MAX_SAFE_INTEGER,
    4294967296,
    Number.NaN,
    Number.POSITIVE_INFINITY,
    randInt(rng, -1000, 5000000000),
    n + randInt(rng, -20, 20),
  ]
  return pick(rng, variants)
}

function mutateFieldValue(rng, key, value) {
  if (key === 'type') return pick(rng, [value, mutateString(rng, value), 'A', 'TXT', 'BOGUS'])
  if (key === 'class') return pick(rng, [value, 'IN', 'CH', 'ANY', 'NONE', '??', randomAscii(rng, 1, 4)])
  if (key === 'ttl') return mutateNumber(rng, value)
  if (/(owner|target|exchange|mname|rname|signer|hostname|mailbox)/i.test(key)) {
    return pick(rng, [randomDomain(rng, true), randomDomain(rng, false), mutateString(rng, value)])
  }
  if (Array.isArray(value)) {
    const next = value.slice()
    if (next.length === 0 || rng() < 0.35) next.push(mutateString(rng, 'x'))
    else next[randInt(rng, 0, next.length - 1)] = mutateFieldValue(rng, key, next[0])
    return next
  }
  if (typeof value === 'number') return mutateNumber(rng, value)
  if (typeof value === 'string') return mutateString(rng, value)
  if (typeof value === 'boolean') return !value
  if (value === null || value === undefined) return pick(rng, [undefined, null, '', 0, randomAscii(rng, 1, 12)])
  return pick(rng, [{}, [], mutateString(rng, String(value))])
}

function mutateRecord(rng, canonical) {
  const candidate = structuredClone(canonical)
  const keys = Object.keys(candidate)
  if (keys.length === 0) return candidate
  const edits = randInt(rng, 1, Math.min(5, keys.length))
  for (let i = 0; i < edits; i++) {
    const key = pick(rng, keys)
    candidate[key] = mutateFieldValue(rng, key, candidate[key])
    if (rng() < 0.08) candidate[key] = undefined
  }
  return candidate
}

function isInterestingFailure(err) {
  if (!(err instanceof Error)) return true
  return ['TypeError', 'RangeError', 'ReferenceError', 'SyntaxError'].includes(err.name)
}

function fuzzClass(rng, TypeClass, iterations) {
  const stats = {
    className: TypeClass.typeName,
    iterations,
    attempts: 0,
    ctorRejected: 0,
    parserRejected: 0,
    interestingFailures: [],
  }

  const canonical = new TypeClass(null).getCanonical()
  const seedRecord = new TypeClass(canonical)
  const seedBind = seedRecord.toBind()
  const seedTiny = seedRecord.toTinydns()
  const seedWire = seedRecord.toWire()

  for (let i = 0; i < iterations; i++) {
    const candidate = mutateRecord(rng, canonical)
    stats.attempts++
    let rr
    try {
      rr = new TypeClass(candidate)
    } catch (err) {
      stats.ctorRejected++
      if (isInterestingFailure(err)) {
        stats.interestingFailures.push({
          op: 'constructor',
          message: err?.message ?? String(err),
          sample: JSON.stringify(candidate),
        })
      }
    }

    const bindInput = mutateString(rng, seedBind)
    const tinyInput = mutateString(rng, seedTiny)
    const wireInput = rng() < 0.5 ? seedWire : new Uint8Array(randInt(rng, 0, 32))

    try {
      TypeClass.fromBind(bindInput)
    } catch (err) {
      stats.parserRejected++
      if (isInterestingFailure(err)) {
        stats.interestingFailures.push({
          op: 'fromBind',
          message: err?.message ?? String(err),
          sample: bindInput,
        })
      }
    }

    try {
      TypeClass.fromTinydns(tinyInput)
    } catch (err) {
      stats.parserRejected++
      if (isInterestingFailure(err)) {
        stats.interestingFailures.push({
          op: 'fromTinydns',
          message: err?.message ?? String(err),
          sample: tinyInput,
        })
      }
    }

    try {
      TypeClass.fromWire(wireInput)
    } catch (err) {
      stats.parserRejected++
      if (isInterestingFailure(err)) {
        stats.interestingFailures.push({
          op: 'fromWire',
          message: err?.message ?? String(err),
          sample: Array.from(wireInput).join(','),
        })
      }
    }

    if (!rr) continue
    try {
      TypeClass.fromBind(rr.toBind())
      TypeClass.fromTinydns(rr.toTinydns())
      TypeClass.fromWire(rr.toWire())
    } catch (err) {
      if (isInterestingFailure(err)) {
        stats.interestingFailures.push({
          op: 'roundtrip',
          message: err?.message ?? String(err),
          sample: JSON.stringify(rr.toJSON()),
        })
      }
    }
  }

  return stats
}

const allExports = Object.values(RRTypes)
const classes = allExports
  .filter((x) => typeof x === 'function' && x !== RR)
  .filter((x) => x.prototype instanceof RR)
  .filter((x) => typeof x.typeName === 'string')

if (classes.length === 0) {
  throw new Error('No RR classes found to fuzz')
}

const rng = makeRng(SEED)
const perClass = []
for (const TypeClass of classes) perClass.push(fuzzClass(rng, TypeClass, ITERATIONS))

const totalInteresting = perClass.reduce((n, r) => n + r.interestingFailures.length, 0)
const totalAttempts = perClass.reduce((n, r) => n + r.attempts, 0)
const totalCtorRejects = perClass.reduce((n, r) => n + r.ctorRejected, 0)
const totalParserRejects = perClass.reduce((n, r) => n + r.parserRejected, 0)

console.log(`fuzz seed=${SEED} iterations=${ITERATIONS} classes=${classes.length}`)
console.log(
  `attempts=${totalAttempts} ctor_rejects=${totalCtorRejects} parser_rejects=${totalParserRejects} interesting_failures=${totalInteresting}`,
)

for (const row of perClass) {
  if (row.interestingFailures.length === 0) continue
  console.log(`\n${row.className}: ${row.interestingFailures.length} interesting failures`)
  for (const f of row.interestingFailures.slice(0, 4)) {
    console.log(`  - [${f.op}] ${f.message}`)
    console.log(`    sample: ${f.sample}`)
  }
}

if (totalInteresting > 0) process.exitCode = 1
