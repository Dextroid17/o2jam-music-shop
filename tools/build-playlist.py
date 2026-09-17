#!/usr/bin/env python3
"""Build the client's OJNList.dat (the song list the game and the Music Shop read).

Layout (little endian), as parsed by O2JamMusicListLoader:
    u32  count          then count * 300 bytes   = the first 300 bytes of each .ojn
    u32  newCount       then newCount * 16 bytes { id, isNew, 0, 0 }
    u32  premiumCount   then premiumCount * 16 bytes { id, gemPrice, 0, 0 }

Every song that has a chart in the shop library is listed, so the in-game Music
Shop offers it for download; songs already installed show up as Playable.
"""
import argparse, os, shutil, struct, sys

H = os.path.expanduser('~')


def entries_from_library(root):
    music = os.path.join(root, 'Patch', 'MUSIC')
    out = {}
    for f in sorted(os.listdir(music)):
        if not f.lower().endswith('.ojn'):
            continue
        p = os.path.join(music, f)
        with open(p, 'rb') as fh:
            head = fh.read(300)
        if len(head) < 300:
            print('skip (short header): %s' % f, file=sys.stderr)
            continue
        out[struct.unpack_from('<i', head, 0)[0]] = head
    return out


def read_sections(path):
    """Read an existing list to preserve its 'new' / 'premium' markers."""
    if not os.path.exists(path):
        return {}, []
    d = open(path, 'rb').read()
    count = struct.unpack_from('<i', d, 0)[0]
    off = 4 + 300 * count
    new, premium = [], []
    try:
        newCount = struct.unpack_from('<i', d, off)[0]
        off += 4
        for _ in range(newCount):
            e = struct.unpack_from('<4I', d, off)
            new.append(e)
            off += 16
        premiumCount = struct.unpack_from('<i', d, off)[0]
        off += 4
        for _ in range(premiumCount):
            premium.append(struct.unpack_from('<4I', d, off))
            off += 16
    except Exception:
        pass
    return {e[0]: e for e in new}, premium


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--shop', default=f'{H}/o2jam/shop')
    ap.add_argument('--target', default=f'{H}/o2jam/native/CXO2/assets/OJNList.dat')
    ap.add_argument('--no-backup', action='store_true')
    a = ap.parse_args()

    entries = entries_from_library(a.shop)
    if not entries:
        sys.exit('no charts found in %s/Patch/MUSIC' % a.shop)

    new_map, premium = read_sections(a.target)
    ids = sorted(entries)

    if not a.no_backup and os.path.exists(a.target) and not os.path.exists(a.target + '.original'):
        shutil.copy2(a.target, a.target + '.original')
        print('backup: %s.original' % a.target)

    blob = bytearray(struct.pack('<I', len(ids)))
    for i in ids:
        blob += entries[i]

    new = [(i, 1, 0, 0) for i in ids]          # everything is offered in the shop
    blob += struct.pack('<I', len(new))
    for e in new:
        blob += struct.pack('<4I', *e)

    premium = [e for e in premium if e[0] in entries]
    blob += struct.pack('<I', len(premium))
    for e in premium:
        blob += struct.pack('<4I', *e)

    open(a.target, 'wb').write(bytes(blob))
    print('wrote %s' % a.target)
    print('  songs listed : %d  (ids %d-%d)' % (len(ids), ids[0], ids[-1]))
    print('  size         : %d bytes' % len(blob))
    print('  new section  : %d   premium section: %d' % (len(new), len(premium)))


if __name__ == '__main__':
    main()
