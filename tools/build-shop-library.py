#!/usr/bin/env python3
"""Build the Music Shop server root:  <root>/Patch/MUSIC/  with every song file we own.

Sources are scanned in priority order; the first copy of a song wins.  Files are
symlinked (not copied) so the shop costs no extra disk space.
"""
import os, sys, json, re, argparse

H = os.path.expanduser('~')

DEFAULT_SOURCES = [
    f'{H}/o2jam/native/CXO2/assets/Music',            # what the client plays today
    f'{H}/o2jam/songlib-2008/Music',                  # recovered 2008 final client library
    f'{H}/o2jam/interval-client/installed/Musi1',     # big Interval library (708 songs)
    f'{H}/o2jam/interval-client/installed/Musi2',     # big Interval library (516 songs)
    f'{H}/o2jam/clients',                             # any older client backups
    f'{H}/o2jam/ph-complete',
]
NAME = re.compile(r'^o2ma(\d+)\.(ojn|ojm)$', re.I)


def collect(sources):
    songs = {}
    for src in sources:
        if not os.path.isdir(src):
            continue
        for root, dirs, files in os.walk(src):
            for f in files:
                m = NAME.match(f)
                if not m:
                    continue
                p = os.path.join(root, f)
                if os.path.islink(p) and not os.path.exists(p):
                    continue
                i, ext = int(m.group(1)), m.group(2).lower()
                songs.setdefault(i, {})[ext] = p
    return songs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=f'{H}/o2jam/shop')
    ap.add_argument('--source', action='append', default=None)
    ap.add_argument('--copy', action='store_true', help='copy files instead of symlinking')
    a = ap.parse_args()

    sources = a.source or DEFAULT_SOURCES
    music = os.path.join(a.root, 'Patch', 'MUSIC')
    os.makedirs(music, exist_ok=True)

    songs = collect(sources)
    linked = skipped = 0
    index = {}
    for i in sorted(songs):
        for ext, src in sorted(songs[i].items()):
            dest = os.path.join(music, f'o2ma{i}.{ext}')
            if os.path.exists(dest):
                skipped += 1
                continue
            if a.copy:
                import shutil
                shutil.copy2(src, dest)
            else:
                os.symlink(os.path.relpath(src, music), dest)
            linked += 1
        index[i] = {e: os.path.getsize(s) for e, s in songs[i].items()}

    json.dump(index, open(os.path.join(a.root, 'index.json'), 'w'), indent=0)
    print(f'shop root     : {a.root}')
    print(f'Patch/MUSIC   : {music}')
    print(f'songs (charts): {len(index)}')
    print(f'files linked  : {linked}   already present: {skipped}')
    both = sum(1 for v in index.values() if 'ojn' in v and 'ojm' in v)
    print(f'complete pairs: {both}   chart-only: {sum(1 for v in index.values() if "ojn" in v and "ojm" not in v)}')


if __name__ == '__main__':
    main()
