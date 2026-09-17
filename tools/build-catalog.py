#!/usr/bin/env python3
"""Build the published song catalogue: catalog.json, songs.csv, CATALOG.md.

Metadata comes from the O2Jam chart (.ojn) headers in the local shop library, so the
level / BPM / note-count values are the real ones the game uses. Nothing here is a song
file: this is a *list*, and the download sources are public archives.
"""
import argparse, csv, json, os, re, struct, sys, urllib.request

H = os.path.expanduser('~')
ARCHIVE_ITEM = 'o2jam_musicpack'
ARCHIVE_BASE = 'https://archive.org/download/%s/' % ARCHIVE_ITEM


def cstr(b):
    return b.split(b'\x00')[0].decode('cp949', 'replace').strip()


def harvest(music_dir):
    songs = {}
    for f in sorted(os.listdir(music_dir)):
        if not f.lower().endswith('.ojn'):
            continue
        with open(os.path.join(music_dir, f), 'rb') as fh:
            h = fh.read(300)
        if len(h) < 300:
            continue
        songs[struct.unpack_from('<i', h, 0)[0]] = {
            'id': struct.unpack_from('<i', h, 0)[0],
            'title': cstr(h[108:172]),
            'artist': cstr(h[172:204]),
            'noter': cstr(h[204:236]),
            'bpm': round(struct.unpack_from('<f', h, 16)[0], 2),
            'levels': list(struct.unpack_from('<hhhh', h, 20)),
            'notes': list(struct.unpack_from('<iii', h, 40)),
        }
    return songs


def archive_index():
    """Which songs are downloadable from the public archive (and from where)."""
    try:
        d = json.load(urllib.request.urlopen('https://archive.org/metadata/' + ARCHIVE_ITEM, timeout=120))
    except Exception as e:
        print('warning: archive lookup failed (%s) - continuing without remote sources' % e, file=sys.stderr)
        return {}
    out = {}
    for f in d['files']:
        m = re.search(r'o2ma(\d+)\.zip$', f['name'], re.I)
        if not m:
            continue
        i = int(m.group(1))
        out.setdefault(i, []).append({'url': ARCHIVE_BASE + urllib.parse.quote(f['name']),
                                      'mirror': f['name'], 'bytes': int(f.get('size') or 0)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--shop', default=f'{H}/o2jam/shop')
    ap.add_argument('--out', default=f'{H}/o2jam-music-shop')
    ap.add_argument('--no-archive', action='store_true')
    a = ap.parse_args()

    music = os.path.join(a.shop, 'Patch', 'MUSIC')
    if not os.path.isdir(music):
        sys.exit('no library at %s' % music)
    os.makedirs(a.out, exist_ok=True)

    songs = harvest(music)
    remote = {} if a.no_archive else archive_index()
    print('songs with metadata : %d' % len(songs))
    print('downloadable (archive): %d' % len(remote))

    for i, s in songs.items():
        s['have'] = True
        if i in remote:
            s['sources'] = remote[i]
    for i, lst in remote.items():
        if i not in songs:
            songs[i] = {'id': i, 'title': None, 'artist': None, 'noter': None, 'bpm': None,
                        'levels': None, 'notes': None, 'have': False, 'sources': lst}

    with open(os.path.join(a.out, 'catalog.json'), 'w') as fh:
        json.dump({'name': 'O2Jam song catalogue', 'count': len(songs),
                   'with_metadata': sum(1 for s in songs.values() if s['title']),
                   'in_library': sum(1 for s in songs.values() if s['have']),
                   'songs': [songs[k] for k in sorted(songs)]}, fh, ensure_ascii=False, indent=1)

    rows = [s for s in (songs[k] for k in sorted(songs)) if s['title']]
    with open(os.path.join(a.out, 'songs.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['id', 'title', 'artist', 'noter', 'bpm', 'level_easy', 'level_normal', 'level_hard', 'level_ex', 'notes_easy', 'notes_normal', 'notes_hard'])
        for s in rows:
            lv = (s['levels'] or [0, 0, 0, 0]) + [0] * (4 - len(s['levels'] or []))
            nt = (s['notes'] or [0, 0, 0]) + [0] * (3 - len(s['notes'] or []))
            w.writerow([s['id'], s['title'], s['artist'], s['noter'], s['bpm'], lv[0], lv[1], lv[2], lv[3], nt[0], nt[1], nt[2]])

    with open(os.path.join(a.out, 'CATALOG.md'), 'w') as fh:
        fh.write('# O2Jam song catalogue\n\n')
        fh.write('%d songs with chart metadata. `EX` is the hardest level of each song.\n\n' % len(rows))
        fh.write('| id | title | artist | BPM | easy | normal | hard | EX |\n')
        fh.write('|---:|---|---|---:|---:|---:|---:|---:|\n')
        for s in rows:
            lv = (s['levels'] or [0, 0, 0, 0]) + [0] * (4 - len(s['levels'] or []))
            t = s['title'].replace('|', '\\|')
            ar = s['artist'].replace('|', '\\|')
            fh.write('| %d | %s | %s | %s | %d | %d | %d | %d |\n' % (s['id'], t, ar, s['bpm'], lv[0], lv[1], lv[2], lv[3]))

    print('wrote catalog.json, songs.csv, CATALOG.md ->', a.out)


if __name__ == '__main__':
    main()
