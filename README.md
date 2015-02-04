# EzyPlyr

EzyPlyr ("easy player") is a simple music player written in Gtk+ 3
using Python. Playback with GStreamer.

## Requirements
For know just `python-gi` version 3.14 and `taglib` (and also it's bindings for Python). Former is is available in Debian (Jessie), Ubuntu 14.10 and probably most modern distros, latter is called `libtag1-dev`.

Install also dependencies from [requirements.txt](./requirements.txt).

## Caution

It's not ready yet. It can play music but only `mp3`. Seeker does not work. You can't rearrange order of songs. Someday it should work, but not yet.

## Future
Listed by importance
- [x] ~~Actual creation of a player~~
- [ ] Storing scanned library and playlist :crying_cat_face:
- [ ] MPRIS v2 support
- [ ] Reading lyrics stored in music file
- [ ] Pluggable interfaces (like in [GMusicBrowser](http://gmusicbrowser.org/))

## FAQ

### This name is stupid. Change it.
[Nah](https://www.youtube.com/watch?v=YYHTMhujUFE).

### Can it even play music?
Yep. But not too much file formats. Not yet. [It's too bad](https://www.youtube.com/watch?v=8sGShK7YNeA).

### Will it support external playlists?
Nah. Not for know. But in the future - [who knows](http://vimeo.com/58229191).
