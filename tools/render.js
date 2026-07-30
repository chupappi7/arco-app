#!/usr/bin/env node
'use strict';

/**
 * render.js — turn post definitions in tools/hooks.json into 1080x1920 JPG
 * slides under drafts/<topic>/, using the templates in tools/slides/ and
 * headless Chrome.
 *
 * Usage:
 *   node tools/render.js              # render every post in hooks.json
 *   node tools/render.js btl          # render one topic
 *   node tools/render.js btl --open   # ...and open the output folder
 *
 * Options:
 *   --hooks PATH   alternate hooks file (default tools/hooks.json)
 *   --out DIR      alternate output root (default drafts/)
 *   --quality N    JPEG quality 1-100 (default 90)
 *   --keep-html    leave the generated HTML in place for debugging
 *   --open         reveal the output folder when done (macOS)
 *
 * Requires: Google Chrome, and `sips` (macOS) for PNG -> JPEG conversion.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync, spawn, spawnSync } = require('child_process');

const REPO_ROOT = path.resolve(__dirname, '..');
const SLIDES_DIR = path.join(__dirname, 'slides');
const BG_DIR = path.join(SLIDES_DIR, 'bg');
const WIDTH = 1080;
const HEIGHT = 1920;
const SHOT_TIMEOUT_MS = 45000;
const POLL_MS = 150;

const CHROME_CANDIDATES = [
  process.env.CHROME_PATH,
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Chromium.app/Contents/MacOS/Chromium',
  '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
  '/usr/bin/google-chrome',
  '/usr/bin/chromium',
].filter(Boolean);

function findChrome() {
  for (const p of CHROME_CANDIDATES) {
    if (fs.existsSync(p)) return p;
  }
  throw new Error(
    'could not find Chrome. Install Google Chrome or set CHROME_PATH to the binary.'
  );
}

function parseArgs(argv) {
  const opts = {
    topic: null,
    hooks: path.join(__dirname, 'hooks.json'),
    out: path.join(REPO_ROOT, 'drafts'),
    quality: 90,
    keepHtml: false,
    open: false,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    switch (a) {
      case '--hooks': opts.hooks = path.resolve(argv[++i]); break;
      case '--out': opts.out = path.resolve(argv[++i]); break;
      case '--quality': opts.quality = Number(argv[++i]); break;
      case '--keep-html': opts.keepHtml = true; break;
      case '--open': opts.open = true; break;
      case '-h':
      case '--help': opts.help = true; break;
      default:
        if (a.startsWith('-')) throw new Error(`unknown option: ${a}`);
        if (opts.topic) throw new Error(`unexpected argument: ${a}`);
        opts.topic = a;
    }
  }
  return opts;
}

function usage() {
  console.log(`
Usage: node tools/render.js [topic] [options]

  --hooks PATH   alternate hooks file (default tools/hooks.json)
  --out DIR      output root (default drafts/)
  --quality N    JPEG quality 1-100 (default 90)
  --keep-html    keep generated HTML for debugging
  --open         reveal the output folder when done
`);
}

/** Resolve a background reference to a file:// URL, or null if unavailable. */
function resolveBackground(ref, warnings) {
  if (!ref) return null;

  // Allow absolute/relative paths as well as bare filenames in slides/bg/.
  const candidates = [
    path.isAbsolute(ref) ? ref : null,
    path.join(BG_DIR, ref),
    path.join(REPO_ROOT, ref),
  ].filter(Boolean);

  for (const c of candidates) {
    if (fs.existsSync(c)) return `file://${encodeURI(c)}`;
  }

  warnings.add(ref);
  return null;
}

const PLACEHOLDER = '__SLIDE_DATA__';

function buildHtml(template, data) {
  // JSON.stringify output is embedded in a <script>; neutralise the one
  // sequence that could break out of it.
  const json = JSON.stringify(data).replace(/<\//g, '<\\/');
  if (!template.includes(PLACEHOLDER)) {
    throw new Error(`template is missing the ${PLACEHOLDER} placeholder`);
  }
  // replaceAll with a function: substitutes every occurrence (templates may
  // mention the token more than once) and stops `$&`-style sequences inside
  // the JSON from being treated as replacement patterns.
  return template.replaceAll(PLACEHOLDER, () => json);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/**
 * Screenshot one HTML file.
 *
 * Chrome 150's `--headless=new` writes the screenshot promptly but then never
 * exits, so spawnSync would block forever. Instead: spawn detached, wait for
 * the PNG to appear and stop growing, then reap the process ourselves.
 */
async function shoot(chrome, htmlPath, pngPath) {
  fs.rmSync(pngPath, { force: true });

  // A fresh profile per shot — we SIGKILL Chrome, which would otherwise leave
  // a stale SingletonLock behind in a shared profile directory.
  const profileDir = fs.mkdtempSync(path.join(os.tmpdir(), 'arco-chrome-'));

  const args = [
    '--headless=new',
    '--disable-gpu',
    '--hide-scrollbars',
    '--force-device-scale-factor=1',
    '--allow-file-access-from-files',
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-extensions',
    // Advance virtual time so webfonts and the background image settle before
    // the frame is captured; virtual time runs faster than wall-clock.
    '--virtual-time-budget=5000',
    `--user-data-dir=${profileDir}`,
    `--window-size=${WIDTH},${HEIGHT}`,
    `--screenshot=${pngPath}`,
    `file://${encodeURI(htmlPath)}`,
  ];

  const child = spawn(chrome, args, { stdio: ['ignore', 'ignore', 'pipe'] });
  let stderr = '';
  child.stderr.on('data', (d) => {
    stderr += d.toString();
  });

  let launchError = null;
  child.on('error', (err) => {
    launchError = err;
  });

  const deadline = Date.now() + SHOT_TIMEOUT_MS;
  let lastSize = -1;
  let stable = 0;

  try {
    while (Date.now() < deadline) {
      await sleep(POLL_MS);
      if (launchError) throw new Error(`chrome failed to launch: ${launchError.message}`);

      if (fs.existsSync(pngPath)) {
        const size = fs.statSync(pngPath).size;
        // Two consecutive identical non-zero sizes means the write finished.
        if (size > 0 && size === lastSize) {
          if (++stable >= 2) return;
        } else {
          stable = 0;
        }
        lastSize = size;
      } else if (child.exitCode !== null) {
        throw new Error(`chrome exited (code ${child.exitCode}) without writing a screenshot.\n${stderr.slice(0, 800)}`);
      }
    }
    throw new Error(`timed out after ${SHOT_TIMEOUT_MS}ms waiting for chrome.\n${stderr.slice(0, 800)}`);
  } finally {
    if (child.exitCode === null) child.kill('SIGKILL');
    fs.rmSync(profileDir, { recursive: true, force: true });
  }
}

function toJpeg(pngPath, jpgPath, quality) {
  try {
    execFileSync(
      'sips',
      ['-s', 'format', 'jpeg', '-s', 'formatOptions', String(quality), pngPath, '--out', jpgPath],
      { stdio: 'ignore' }
    );
  } catch (err) {
    throw new Error(
      `sips failed to convert ${path.basename(pngPath)} to JPEG (${err.message}). ` +
        `sips ships with macOS; on other platforms convert the PNGs yourself.`
    );
  }
}

function slidesFor(post, defaults) {
  return post.slides.map((slide, i) => {
    const type = slide.type || 'text';
    if (type === 'cta') {
      return {
        type,
        bg: slide.bg,
        icon: slide.icon || defaults.cta?.icon || 'icon.png',
        appName: slide.appName || defaults.cta?.appName || '',
        subtitle: slide.subtitle || defaults.cta?.subtitle || '',
      };
    }
    // A text slide is just an ordered list of paragraphs.
    const paragraphs = Array.isArray(slide.text) ? slide.text : [slide.text];
    if (paragraphs.some((p) => typeof p !== 'string')) {
      throw new Error(`slide ${i + 1}: "text" must be a string or an array of strings`);
    }
    const align = slide.align || 'top';
    if (!['top', 'center', 'low'].includes(align)) {
      throw new Error(`slide ${i + 1}: "align" must be one of top, center, low`);
    }
    return { type, bg: slide.bg, paragraphs, align };
  });
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) return usage();

  if (!fs.existsSync(opts.hooks)) {
    throw new Error(`no hooks file at ${path.relative(REPO_ROOT, opts.hooks)}`);
  }
  const hooks = JSON.parse(fs.readFileSync(opts.hooks, 'utf8'));
  const defaults = hooks.defaults || {};

  let posts = hooks.posts || [];
  if (opts.topic) {
    posts = posts.filter((p) => p.topic === opts.topic);
    if (posts.length === 0) {
      const known = (hooks.posts || []).map((p) => p.topic).join(', ');
      throw new Error(`no post with topic "${opts.topic}" in hooks.json.\n  known topics: ${known}`);
    }
  }
  if (posts.length === 0) throw new Error('hooks.json has no posts');

  const chrome = findChrome();
  const templates = {
    text: fs.readFileSync(path.join(SLIDES_DIR, 'text.html'), 'utf8'),
    cta: fs.readFileSync(path.join(SLIDES_DIR, 'cta.html'), 'utf8'),
  };

  const missingBackgrounds = new Set();
  let rendered = 0;

  for (const post of posts) {
    const outDir = path.join(opts.out, post.topic);
    fs.mkdirSync(outDir, { recursive: true });

    const slides = slidesFor(post, defaults);
    console.log(`\n${post.topic}  (${slides.length} slides -> ${path.relative(REPO_ROOT, outDir)}/)`);

    for (const [i, slide] of slides.entries()) {
      const n = String(i + 1).padStart(2, '0');
      const template = templates[slide.type];
      if (!template) throw new Error(`unknown slide type "${slide.type}" in topic ${post.topic}`);

      const data = { bg: resolveBackground(slide.bg, missingBackgrounds) };
      if (slide.type === 'cta') {
        data.icon = resolveBackground(slide.icon, missingBackgrounds) || '';
        data.appName = slide.appName;
        data.subtitle = slide.subtitle;
      } else {
        data.paragraphs = slide.paragraphs;
        data.align = slide.align;
      }

      // Written inside slides/ so ./base.css, ./fonts and ./bg resolve.
      const htmlPath = path.join(SLIDES_DIR, `.render-${post.topic}-${n}.html`);
      const pngPath = path.join(outDir, `${n}.png`);
      const jpgPath = path.join(outDir, `${n}.jpg`);

      fs.writeFileSync(htmlPath, buildHtml(template, data));
      try {
        await shoot(chrome, htmlPath, pngPath);
        toJpeg(pngPath, jpgPath, opts.quality);
        fs.unlinkSync(pngPath);
      } finally {
        if (!opts.keepHtml) fs.rmSync(htmlPath, { force: true });
      }

      const kb = (fs.statSync(jpgPath).size / 1024).toFixed(0);
      console.log(`  ${n}.jpg  ${slide.type.padEnd(4)}  ${kb}KB`);
      rendered++;
    }
  }

  console.log(`\nrendered ${rendered} slide(s) at ${WIDTH}x${HEIGHT}`);

  if (missingBackgrounds.size) {
    console.warn(
      `\n! ${missingBackgrounds.size} background image(s) not found — those slides used the ` +
        `placeholder gradient:\n    ${[...missingBackgrounds].join('\n    ')}\n` +
        `  Drop the files into tools/slides/bg/ and re-run.`
    );
  }

  if (opts.open && process.platform === 'darwin') {
    spawnSync('open', [opts.topic ? path.join(opts.out, opts.topic) : opts.out]);
  }
}

main().catch((err) => {
  console.error(`\nERROR  ${err.message}`);
  process.exit(1);
});
