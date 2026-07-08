/**
 * Post-build: inject content_security_policy into dist-crx/manifest.json.
 *
 * Chrome MV3 default CSP blocks blob: workers,
 * which prevents PDF.js (vue-pdf-embed) from rendering PDFs.
 *
 * @crxjs/vite-plugin strips CSP during build,
 * so we inject it after the fact.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

const manifestPath = resolve(process.cwd(), 'dist-crx', 'manifest.json');
const raw = readFileSync(manifestPath, 'utf8');
const manifest = JSON.parse(raw);

manifest.content_security_policy = {
  extension_pages:
    "script-src 'self'; object-src 'self'; worker-src 'self' blob:"
};

writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n', 'utf8');
console.log('[inject-crx-csp] CSP injected into dist-crx/manifest.json');
