# O2Jam Music Shop 🎵

Ever opened the **MUSIC SHOP** in the offline O2Jam client, seen 100+ pages of songs, pressed
**DOWN!** … and nothing happened? That is because the shop fetches songs from the old patch
server over FTP/SFTP, and that server has been gone for years.

This repo fixes that, with two pieces:

1. **The catalogue** - `catalog.json` / `songs.csv` / [CATALOG.md](CATALOG.md) list every song the
   game knows about (id, title, artist, BPM, levels, note counts) plus where each one can be
   fetched from. 1,231 songs carry full chart metadata; 2,307 have a public mirror.
2. **The shop server** - `tools/` serves a plain folder over HTTP in exactly the layout the
   client asks for, and a small client patch teaches the shop to speak HTTP instead of FTP.

Song names that were only ever stored in Korean / Japanese / Chinese are **translated to
English, with the original language in parentheses** - e.g. `Umbrella (Feat. Younha) (KO)`,
`Nunchaku (CN)`, `Tori no Uta (JP)`. The game's own font has no CJK glyphs, so those titles
used to draw as empty boxes; the English form fixes that everywhere (shop list, song list,
catalogue). The same treatment is applied to artist and note-arranger names.

The language tags are deliberately **two letters** - `(KO)` `(CN)` `(JP)`. The in-game MY MUSIC
list only has room for about 30 characters per row, so the short form buys back five characters
and stops long titles from clipping with an ellipsis.

Result: the in-game shop really downloads songs, and they become playable straight away.

## Quick start

```bash
# 1. put your own song files into the shop library (paths are configurable)
python3 tools/build-shop-library.py --root ~/o2jam/shop

# 2. write the song list the client + shop read
python3 tools/build-playlist.py   --shop ~/o2jam/shop

# 3. start serving, then launch the client with the shop enabled
tools/shop-up.sh start
O2JAM_SHOP_URL=http://127.0.0.1:8099 ./bin/linux/Release/OTwo
```

In game: **enter a room -> MUSIC SHOP -> MY MUSIC -> tick a song -> DOWN!**

## How it works

```
   Music Shop UI (client)                     shop server (this repo)
   ---------------------                      -----------------------
   song list  <-- OJNList.dat                 /Patch/MUSIC/o2ma602.ojn
   tick a row --> queue++                     /Patch/MUSIC/o2ma602.ojm
   DOWN!      --> MusicDownloaderService  --> HTTP HEAD (size) + GET (file)
                  writes Music/TEMP/*_  --> renames into Music/
                  => song appears as Playable
```

The original client downloaded from `ftp://<host>/Patch/MUSIC/` (anonymous login) or the same
path over SFTP. The patch in `patches/` adds an HTTP path that is used when `O2JAM_SHOP_URL` is
set, so **any static host works**: a local Python server, nginx, a NAS, a web host, S3, GitHub
raw. FTP/SFTP behaviour is untouched.

### What the client patch changes

* `MusicDownloaderService`: new `DownloadProcHttp()` - HEAD for sizes, GET for the files, same
  progress/notification flow as the original protocol (so the shop UI shows speed, counts and
  "Downloading of a file is completed").
* `StateMusicShop`: two upstream bugs that made the shop's list unclickable - the row click
  callback was only registered when a tick-box child already existed, and a click on the tick
  box was swallowed instead of toggling the queue. Now clicking a row or its box enqueues it.

See [docs/HOW-IT-WORKS.md](docs/HOW-IT-WORKS.md) for the file formats (including the
`OJNList.dat` layout with its `new` / `premium` sections) and the wire protocol.

## No songs in this repo

This repository contains **no game data** - no charts, no audio, no textures. It is a
catalogue (metadata) plus tooling. `build-shop-library.py` indexes the song files **you**
already have, and the downloadable mirrors point at public archives. O2Jam, its songs and its
charts belong to their respective owners (O2Media / Nowcom and the original artists and
noters); please own the game legally if you use this.

## Credits

* Song metadata is read straight out of your own `.ojn` chart headers.
* Public mirrors: the Internet Archive `o2jam_musicpack` item (per-song zips).
* The client is [CXO2](https://github.com/CXO2/CXO2) (no licence upstream - so this repo ships
  only our own patches, never their code).

Vibe-coded with Hermes Agent. 🎧
