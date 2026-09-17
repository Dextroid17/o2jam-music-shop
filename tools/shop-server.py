#!/usr/bin/env python3
"""O2Jam Music Shop — static HTTP server for the in-game shop.

Serves a song library laid out exactly like the original O2Media patch server:

    <root>/Patch/MUSIC/o2ma<ID>.ojn
    <root>/Patch/MUSIC/o2ma<ID>.ojm

The patched OTwo client downloads from <base>/Patch/MUSIC/... (see
MusicDownloaderService::DownloadProcHttp) so anything that can serve static files
can host the shop: this script, `python -m http.server`, nginx, a NAS, GitHub raw...

Usage:
    python3 shop-server.py --root ~/o2jam/shop --port 8099
"""
import argparse, functools, http.server, os, socketserver, sys, time

ROOT = os.path.expanduser('~/o2jam/shop')


class ShopHandler(http.server.SimpleHTTPRequestHandler):
    server_version = 'O2JamMusicShop/1.0'
    protocol_version = 'HTTP/1.1'

    def log_message(self, fmt, *args):
        sys.stderr.write('%s  %s  %s\n' % (time.strftime('%H:%M:%S'), self.address_string(), fmt % args))

    def end_headers(self):
        # the client asks for sizes with HEAD and then GETs the same path
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Accept-Ranges', 'none')
        super().end_headers()


class ThreadedServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=ROOT)
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=8099)
    a = ap.parse_args()

    root = os.path.abspath(os.path.expanduser(a.root))
    if not os.path.isdir(os.path.join(root, 'Patch', 'MUSIC')):
        sys.exit('no %s/Patch/MUSIC — build the library first (build-shop-library.py)' % root)

    handler = functools.partial(ShopHandler, directory=root)
    songs = len([f for f in os.listdir(os.path.join(root, 'Patch', 'MUSIC')) if f.endswith('.ojn')])
    print('O2Jam Music Shop on http://%s:%d  (root %s, %d songs)' % (a.host, a.port, root, songs))
    with ThreadedServer((a.host, a.port), handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
