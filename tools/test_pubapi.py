import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import pubapi


class Fake(BaseHTTPRequestHandler):
    calls = []

    def log_message(self, *a):
        pass

    def _reply(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _record(self):
        n = int(self.headers.get('Content-Length') or 0)
        raw = self.rfile.read(n) if n else b''
        Fake.calls.append({'method': self.command, 'path': self.path, 'auth': self.headers.get('Authorization'),
                           'type': self.headers.get('Content-Type'), 'raw': raw})
        return raw

    def do_GET(self):
        self._record()
        if self.path == '/v1/accounts':
            return self._reply(200, {'accounts': [{'id': 'acc_a', 'username': 'arco.app'},
                                                  {'id': 'acc_b', 'username': 'getarcoapp'}]})
        if self.path.startswith('/v1/posts'):
            return self._reply(200, {'posts': []})
        return self._reply(404, {'error': 'Not found'})

    def do_POST(self):
        raw = self._record()
        if self.path == '/v1/media':
            return self._reply(200, {'key': f'ws_1/{len(Fake.calls)}.jpg'})
        if self.path == '/v1/posts':
            body = json.loads(raw)
            if not body['settings'].get('privacy_level'):
                return self._reply(400, {'error': 'Choose who can view this post'})
            return self._reply(200, {'id': 'pst_1', **body})
        return self._reply(404, {'error': 'Not found'})


class PubApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(('127.0.0.1', 0), Fake)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.api = pubapi.PubAPI(f'http://127.0.0.1:{cls.srv.server_port}/v1', 'apk_test')

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        Fake.calls.clear()

    def test_account_ids_match_on_username(self):
        ids = pubapi.account_ids(self.api, [{'key': 'vn', 'label': 'arco.app'},
                                            {'key': 'getarco', 'label': 'getarcoapp'},
                                            {'key': 'us', 'label': 'emiliagonzalez389'}])
        self.assertEqual(ids, {'vn': 'acc_a', 'getarco': 'acc_b'})
        self.assertEqual(Fake.calls[0]['auth'], 'Key apk_test')

    def test_api_settings_maps_panel_keys(self):
        self.assertEqual(pubapi.api_settings({'privacy': 'SELF_ONLY', 'disable_comment': True}),
                         {'privacy_level': 'SELF_ONLY', 'disable_comment': True, 'auto_add_music': False,
                          'brand_organic': False, 'branded_content': False})

    def test_send_topic_uploads_slides_in_order_then_creates_the_post(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, 'drafts', 'my-topic'))
            for name in ('10.jpg', '2.jpg', '1.jpg', 'notes.txt'):
                with open(os.path.join(d, 'drafts', 'my-topic', name), 'wb') as f:
                    f.write(b'\xff\xd8\xff' + name.encode())
            hooks = os.path.join(d, 'hooks.json')
            with open(hooks, 'w') as f:
                json.dump({'posts': [{'topic': 'my-topic', 'title': 'Hook', 'caption': 'Cap'}]}, f)
            post = pubapi.send_topic(self.api, 'acc_a', os.path.join(d, 'drafts'), hooks, 'my-topic',
                                     {'privacy': 'PUBLIC_TO_EVERYONE'}, scheduled_at=1_900_000_000)
        uploads = [c for c in Fake.calls if c['path'] == '/v1/media']
        self.assertEqual([c['raw'][3:] for c in uploads], [b'1.jpg', b'2.jpg', b'10.jpg'])
        self.assertTrue(all(c['type'] == 'image/jpeg' for c in uploads))
        self.assertEqual(post['title'], 'Hook')
        self.assertEqual(post['caption'], 'Cap')
        self.assertEqual(post['scheduled_at'], 1_900_000_000)
        self.assertEqual(len(post['image_keys']), 3)

    def test_title_caption_falls_back_to_the_slug(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(pubapi.title_caption(os.path.join(d, 'missing.json'), 'best-for-last-5'),
                             ('Best For Last 5', ''))

    def test_errors_carry_the_server_message(self):
        with self.assertRaises(pubapi.PubError) as ctx:
            self.api.create_post('acc_a', ['k'], 't', 'c', {'privacy_level': ''})
        self.assertEqual(str(ctx.exception), 'Choose who can view this post')
        self.assertEqual(ctx.exception.status, 400)


class ScheduleManyTest(unittest.TestCase):
    def test_keeps_what_went_through_when_a_later_account_fails(self):
        calls = []

        def send(topic, key, st, when):
            calls.append((key, when))
            if key == 'us':
                raise pubapi.PubError('@emiliagonzalez389 is not connected')
            return {'id': 'pst_' + key}

        sent, error = pubapi.schedule_many(send, 'my-topic', ['vn', 'getarco', 'us', 'max'], 1000, 2, {})
        self.assertEqual(sorted(sent), ['getarco', 'vn'])
        self.assertEqual(sent['getarco']['id'], 'pst_getarco')
        self.assertIn('us', error)
        self.assertIn('not connected', error)
        self.assertEqual(calls, [('vn', 1000), ('getarco', 1120), ('us', 1240)])

    def test_no_error_when_all_succeed(self):
        sent, error = pubapi.schedule_many(lambda *a: {'id': 'p'}, 't', ['vn'], 5, 0, {})
        self.assertEqual((list(sent), error), (['vn'], None))


if __name__ == '__main__':
    unittest.main()
