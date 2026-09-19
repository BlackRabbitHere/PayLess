// Test-only HTTP replay of committed scraper wire fixtures. Never used by the product.
import { createServer } from 'node:http'
import { readFile } from 'node:fs/promises'
let mode = 'normal'
createServer(async (request, response) => {
  response.setHeader('Content-Type', 'application/json')
  if (request.url === '/health') { response.end(JSON.stringify({ schemaVersion: 1, status: 'ok', mode: 'fixture' })); return }
  let text = ''
  for await (const chunk of request) text += chunk
  if (request.url === '/__control') { mode = JSON.parse(text).mode; response.end('{}'); return }
  const input = JSON.parse(text || '{}')
  if (mode === 'unavailable' || (mode === 'partial' && input.provider === 'YATRA')) {
    response.statusCode = 503; response.end(JSON.stringify({ detail: 'Controlled test provider failure' })); return
  }
  const names = { GYFTR: 'gyftr_swiggy', YATRA: 'yatra_yatra', EASEMYTRIP: 'easemytrip_easemytrip' }
  if (!names[input.provider]) { response.statusCode = 400; response.end('{}'); return }
  response.end(await readFile(new URL('../data/fixtures/scraper/' + names[input.provider] + '.json', import.meta.url)))
}).listen(18000, '127.0.0.1')
