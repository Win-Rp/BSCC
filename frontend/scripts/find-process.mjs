import { readFileSync } from 'node:fs';

console.log('Starting search...');
const c = readFileSync('dist-crx/assets/CompareView-DRahlOt4.js', 'utf8');
console.log('File loaded, length:', c.length);
const re = /typeof process\s*==\s*['"]object['"]/;
const m = re.exec(c);
if (m) {
  console.log('Found at', m.index);
  console.log('Context:', c.substring(Math.max(0, m.index - 200), m.index + 400));
} else {
  console.log('typeof process pattern NOT found');
}

// Also find the Ai variable that controls fake worker
const aiMatch = c.match(/Ai\s*=\s*(typeof process[^;]+)/);
if (aiMatch) console.log('Ai definition:', aiMatch[1]);

// Find process references near fake worker
const fakeIdx = c.indexOf('fake worker');
if (fakeIdx >= 0) {
  const searchRegion = c.substring(Math.max(0, fakeIdx - 5000), fakeIdx);
  const procMatch = searchRegion.match(/(\w+)\s*=\s*(typeof process[^;]+)/);
  if (procMatch) console.log('Process check near fake worker:', procMatch[0]);
}
