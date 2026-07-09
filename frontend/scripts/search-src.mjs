import { readFileSync } from 'node:fs';

const c = readFileSync('node_modules/vue-pdf-embed/dist/index.mjs', 'utf8');

// Find data:text/javascript references
let idx = c.indexOf('data:text');
if (idx >= 0) {
  console.log('=== data:text found at', idx, '===');
  console.log(c.substring(Math.max(0, idx - 300), idx + 500));
}

// Find script tag creation near fake worker code
idx = c.indexOf('fake worker');
if (idx >= 0) {
  console.log('\n=== Looking for script creation near fake worker ===');
  // Search backwards for createElement script
  const beforeFake = c.substring(Math.max(0, idx - 10000), idx);
  let scriptIdx = beforeFake.lastIndexOf("createElement");
  while (scriptIdx >= 0) {
    const ctx = c.substring(scriptIdx - 50, scriptIdx + 200);
    console.log('createElement context:', ctx);
    scriptIdx = beforeFake.lastIndexOf("createElement", scriptIdx - 1);
    if (scriptIdx < 0) break;
  }
}

// Find createElement("script") anywhere
console.log('\n=== All createElement("script") occurrences ===');
let pos = 0;
while ((pos = c.indexOf('createElement("script"', pos)) >= 0) {
  console.log('At', pos, ':', c.substring(Math.max(0, pos - 100), Math.min(pos + 300, c.length)));
  pos += 20;
}

// Find variable name for Pd
console.log('\n=== Looking for Pd/Ai ===');
const pdDef = c.match(/(\w+)\s*=\s*typeof process\s*==\s*"object"/);
if (pdDef) console.log('Variable for typeof process check:', pdDef[0]);
