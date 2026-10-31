// Stamps app.html's stylesheet and script URLs with the current commit, so a
// deploy always fetches fresh files instead of what the browser has cached.
//   node publisher/dev/stamp.cjs        (run before `vercel deploy`)
const fs = require('fs'), path = require('path'), { execSync } = require('child_process');
const sha = execSync('git rev-parse --short HEAD', { cwd: __dirname }).toString().trim();
const f = path.join(__dirname, '..', 'public', 'app.html');
const out = fs.readFileSync(f, 'utf8').replace(/\/app\.(css|js)(\?v=[^"]*)?"/g, `/app.$1?v=${sha}"`);
fs.writeFileSync(f, out);
console.log('stamped app.html with', sha);
