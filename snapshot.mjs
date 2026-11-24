import { writeFile, mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';
import { createRequire } from 'node:module';
import { quote } from './server.mjs';
const require = createRequire(import.meta.url),
  L = require('../web/logic.js');
const limit = Number(process.env.SNAPSHOT_LIMIT || 40);
const stocks = L.CATALOG.filter((x) => !['SPY', 'QQQ', 'VOO'].includes(x.ticker)).slice(0, limit);
const result = {
  generatedAt: new Date().toISOString(),
  source: 'Yahoo chart v8 (unofficial), no private portfolio access',
  stocks: [],
  errors: {},
};
for (const [i, s] of stocks.entries()) {
  try {
    const q = await quote(s.ticker);
    result.stocks.push({ ticker: s.ticker, name: s.name, sector: s.sector, layer: s.layer, quote: q });
    console.log(`${i + 1}/${stocks.length} ${s.ticker}: OK`);
  } catch (e) {
    result.errors[s.ticker] = e.message;
    console.log(`${i + 1}/${stocks.length} ${s.ticker}: ${e.message}`);
  }
}
await mkdir(resolve(import.meta.dirname, '../data'), { recursive: true });
await writeFile(resolve(import.meta.dirname, '../data/snapshot.json'), JSON.stringify(result));
console.log(
  'Snapshot público creado:',
  result.stocks.length,
  'cotizaciones,',
  Object.keys(result.errors).length,
  'errores.',
);
