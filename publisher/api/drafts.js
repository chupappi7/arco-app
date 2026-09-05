// The slides to post, read from the public repo that already serves them.
//
// This is what lets the page stand on its own: the images live on GitHub
// Pages (the domain TikTok has verified), and their listing comes from the
// GitHub contents API, so nothing here depends on a machine at home being on.

const OWNER = process.env.GH_OWNER || 'chupappi7';
const REPO = process.env.GH_REPO || 'arco-app';
const PAGES = process.env.PAGES_BASE || `https://${OWNER}.github.io/${REPO}`;

const IMG = /\.(jpe?g|png)$/i;

async function gh(path) {
  const headers = { Accept: 'application/vnd.github+json' };
  // Optional: lifts the unauthenticated 60/hour limit if the deployment sets it.
  if (process.env.GITHUB_TOKEN)
    headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  const r = await fetch(`https://api.github.com/repos/${OWNER}/${REPO}/contents/${path}`, {
    headers,
  });
  if (!r.ok) throw new Error(`GitHub returned ${r.status} for ${path}`);
  return r.json();
}

export default async function handler(req, res) {
  const url = new URL(req.url, 'https://placeholder.invalid');
  const topic = url.searchParams.get('topic');

  try {
    if (!topic) {
      const items = await gh('drafts');
      const topics = items
        .filter(x => x.type === 'dir' && !x.name.startsWith('_'))
        .map(x => x.name)
        .sort();
      // Short cache: the list changes when a post is built, not per request.
      res.setHeader('Cache-Control', 's-maxage=60, stale-while-revalidate=300');
      return res.status(200).json({ topics });
    }

    // A topic is a directory name; anything with a slash is not one.
    if (!/^[A-Za-z0-9._-]+$/.test(topic))
      return res.status(400).json({ error: 'bad topic' });

    const items = await gh(`drafts/${encodeURIComponent(topic)}`);
    const slides = items
      .filter(x => x.type === 'file' && IMG.test(x.name))
      .map(x => x.name)
      .sort()
      .map(name => `${PAGES}/drafts/${topic}/${name}`);
    res.setHeader('Cache-Control', 's-maxage=60, stale-while-revalidate=300');
    res.status(200).json({ topic, slides });
  } catch (err) {
    res.status(502).json({ error: err.message });
  }
}
