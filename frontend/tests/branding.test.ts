import assert from 'node:assert/strict'
import { readdirSync, readFileSync } from 'node:fs'
import { dirname, join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'
import test from 'node:test'
import { BRAND } from '../src/app/config/brand'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const oldBrand = /route[ -]?wise|routwise/i
// Exact compatibility identifiers only; any additional branding on the same line still fails.
const preserved = new Map([
  ['src/features/wallet/controller/walletStore.ts', "'routewise-wallet-v2'"],
  ['src/features/optimization/model/state.ts', "'routewise-demo-v1'"],
])
function sources(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap(entry => entry.isDirectory()
    ? sources(join(directory, entry.name))
    : /\.(tsx?|css|html|svg|json|webmanifest)$/.test(entry.name) ? [join(directory, entry.name)] : [])
}

test('frontend source and browser assets use only the canonical display brand', () => {
  assert.equal(BRAND.name, 'PayLess')
  assert.equal(BRAND.description, 'Smart payment route optimization')
  for (const path of [...sources(join(root, 'src')), ...sources(join(root, 'public')), join(root, 'index.html')]) {
    const key = relative(root, path).replaceAll('\\', '/')
    const source = readFileSync(path, 'utf8')
    const exception = preserved.get(key)
    if (exception) assert.ok(source.includes(exception), `Compatibility key changed: ${key}`)
    assert.doesNotMatch(exception ? source.replace(exception, "'preserved-storage-key'") : source, oldBrand, key)
  }
  const html = readFileSync(join(root, 'index.html'), 'utf8')
  assert.ok(html.includes(`<title>${BRAND.name}</title>`))
  assert.ok(html.includes(`name="application-name" content="${BRAND.name}"`))
})
