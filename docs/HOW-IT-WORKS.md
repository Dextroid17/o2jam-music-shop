# How the shop works (formats + protocol)

## 1. The song list: `assets/OJNList.dat`

Little endian, as parsed by `O2JamMusicListLoader`:

| part | type | meaning |
|---|---|---|
| count | u32 | number of charts |
| charts | count * 300 bytes | the **first 300 bytes of each `.ojn`** (the chart header: id, bpm, level, note counts, title, artist, noter, ojm name) |
| newCount | u32 | then `newCount * 16 bytes` of `{ id, isNew, 0, 0 }` |
| premiumCount | u32 | then `premiumCount * 16 bytes` of `{ id, gemPrice, 0, 0 }` |

The client merges this list with the `o2ma*.ojn` files it finds in `Music/`:

* chart listed **and** a local file whose note counts match -> `Playable`
* chart listed, no local file -> `Missing` -> the shop offers it for download
* chart listed, local file with different note counts -> `Corrupted`

`tools/build-playlist.py` regenerates the list from a library, so every song becomes
advertised in the shop as downloadable. It keeps a `.original` backup the first time.

## 2. The download protocol

The shop needs **two files per song** and asks for their sizes before transferring anything:

```
<base>/Patch/MUSIC/o2ma<ID>.ojn     the chart
<base>/Patch/MUSIC/o2ma<ID>.ojm     the keysounds
```

* original: `HEAD`/`SIZE` + `GET` (FTP, "TYPE I" binary) or SFTP `getAttributes` + `download`,
  anonymous login with `webmaster@o2-media.com`, port 21/22 unless the URL says otherwise.
* this patch: HTTP `HEAD` for `Content-Length`, then `GET`. Set `O2JAM_SHOP_URL` (or pass an
  `http://` FTP argument) and the HTTP path is used; otherwise the original FTP/SFTP code runs
  unchanged.

Files land in `Music/TEMP/<name>_` first, then get renamed to `Music/<name>`; a per-song
`<name>.ini` records the file list and status (the original patch-server convention).

## 3. What the client does with the result

`SessionContext` rescans on the next session: a downloaded chart with matching note counts
becomes `Playable`, so the song leaves the shop's download list and shows up (playable) in the
normal song selection.

## 4. Coordinates for automated testing (Xvfb, 1920x1080)

Planet `Melpomin` (210,480) -> channel row (1700,130) double-click + `Return` -> room list
-> `MUSIC SHOP` (850,30) -> row tick box (1797,172) -> `DOWN!` (1773,582).

Handy: `MusicShop.json` labels the columns; the DOWN column header is a *sort* button, so a
click there re-orders the list instead of selecting a song.
