/**
 * Post-build: inject content_security_policy into dist-crx/manifest.json.
 *
 * Chrome MV3 rejects `blob:` in extension page worker-src.
 * We keep the CSP MV3-safe here and rely on the app code to avoid
 * creating blob-backed workers in extension pages.
 *
 * @crxjs/vite-plugin strips CSP during build, so we inject it after the fact.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

const manifestPath = resolve(process.cwd(), 'dist-crx', 'manifest.json');
const raw = readFileSync(manifestPath, 'utf8');
const manifest = JSON.parse(raw);

manifest.content_security_policy = {
  extension_pages:
    "script-src 'self'; object-src 'self'; worker-src 'self'"
};

writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n', 'utf8');
console.log('[inject-crx-csp] CSP injected into dist-crx/manifest.json');
