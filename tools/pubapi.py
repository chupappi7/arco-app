"""A small client for the ARCO Publisher API (the Cloudflare Worker).

The dashboard is one API client among the tool's users: it uploads a topic's
slides and creates the post, and ARCO Publisher publishes it at the chosen
time with no laptop involved. Standard library only, like the dashboard.
"""
import json
import os
import re
import urllib.error
import urllib.request

TYPES = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png'}


class PubError(Exception):
    def __init__(self, message, status=0):
        super().__init__(message)
        self.status = status


class PubAPI:
    def __init__(self, base, key, timeout=60):
        self.base = base.rstrip('/')
        self.key = key
        self.timeout = timeout

    def _call(self, method, path, body=None, data=None, ctype=None):
        headers = {'Authorization': f'Key {self.key}'}
        if body is not None:
            data, ctype = json.dumps(body).encode(), 'application/json'
        if ctype:
            headers['Content-Type'] = ctype
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                raw = r.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            try:
                msg = json.loads(e.read() or b'{}').get('error')
            except ValueError:
                msg = None
            raise PubError(msg or f'ARCO Publisher returned HTTP {e.code}', e.code) from None
        except urllib.error.URLError as e:
            raise PubError(f'Could not reach ARCO Publisher: {e.reason}') from None

    def accounts(self):
        return self._call('GET', '/accounts')['accounts']

    def creator_info(self, account_id):
        return self._call('GET', f'/accounts/{account_id}/creator-info')

    def upload(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext not in TYPES:
            raise PubError(f'{os.path.basename(path)} is not a JPG or PNG')
        with open(path, 'rb') as f:
            return self._call('POST', '/media', data=f.read(), ctype=TYPES[ext])['key']

    def create_post(self, account_id, image_keys, title, caption, settings, scheduled_at=None):
        return self._call('POST', '/posts', body={
            'account_id': account_id, 'image_keys': image_keys, 'cover_index': 0,
            'title': title, 'caption': caption, 'settings': settings, 'scheduled_at': scheduled_at})

    def list_posts(self, frm, to):
        return self._call('GET', f'/posts?from={int(frm)}&to={int(to)}')['posts']

    def cancel(self, post_id):
        return self._call('DELETE', f'/posts/{post_id}')


def account_ids(api, dashboard_accounts):
    by_name = {a['username']: a['id'] for a in api.accounts()}
    return {a['key']: by_name[a['label']] for a in dashboard_accounts if a['label'] in by_name}


def api_settings(st):
    return {
        'privacy_level': st.get('privacy') or '',
        'disable_comment': bool(st.get('disable_comment')),
        'auto_add_music': bool(st.get('auto_add_music')),
        'brand_organic': bool(st.get('brand_organic')),
        'branded_content': bool(st.get('branded_content')),
    }


def _natural(name):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', name)]


def title_caption(hooks_path, topic):
    try:
        with open(hooks_path) as f:
            posts = json.load(f).get('posts') or []
    except (OSError, ValueError):
        posts = []
    post = next((p for p in posts if p.get('topic') == topic), {})
    title = post.get('title') or re.sub(r'\b\w', lambda m: m.group().upper(), re.sub(r'[-_]+', ' ', topic))
    return title, post.get('caption') or ''


def send_topic(api, account_id, drafts_dir, hooks_path, topic, panel_settings, scheduled_at=None):
    folder = os.path.join(drafts_dir, topic)
    slides = sorted((f for f in os.listdir(folder) if os.path.splitext(f)[1].lower() in TYPES), key=_natural)
    if not slides:
        raise PubError(f'No JPG or PNG slides in drafts/{topic}')
    keys = [api.upload(os.path.join(folder, f)) for f in slides]
    title, caption = title_caption(hooks_path, topic)
    return api.create_post(account_id, keys, title[:90], caption, api_settings(panel_settings), scheduled_at)
