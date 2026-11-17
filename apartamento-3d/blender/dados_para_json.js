const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
eval(src + '\n;globalThis.__OUT = {WALLS, ROOMS, PROP, RAIL, Q1, OUTLINE, HALL, PE_DIREITO, rail: railPts()};');
fs.writeFileSync(process.argv[3], JSON.stringify(globalThis.__OUT));
console.log('ok', Object.keys(globalThis.__OUT).join(','));
