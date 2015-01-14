import locale
import logging
import os.path

import taglib
from gi.repository import GObject


logger = logging.getLogger()


class MusicBase(GObject.GObject):
    def __init__(self, **kwargs):
        super(MusicBase, self).__init__()
        self.set_properties(**kwargs)


class Song(MusicBase):
    path = GObject.property(type=str)
    track_no = GObject.property(type=int)
    title = GObject.property(type=str)
    artist = GObject.property(type=str)
    album = GObject.property(type=str)
    album_artist = GObject.property(type=str)
    year = GObject.property(type=str)
    genre = GObject.property(type=str)

    def __init__(self, path=None, *args, **kwargs):
        try:
            track = taglib.File(path)
            tags = track.tags

            title = tags.get('TITLE', (os.path.basename(path,)))[0]
            track_no = track_no = tags.get('TRACKNUMBER', ('0',))[0]
            track_no = int(''.join(d for d in track_no if d.isdigit()))
            year = tags.get('DATE', (0,))[0]
            artist = tags.get('ARTIST', ('',))[0]
            album = tags.get('ALBUM', ('',))[0]
            genre = tags.get('GENRE', ('',))[0]
            album_artist = tags.get('ALBUMARTIST', ('',))[0]
        except TypeError:
            logger.debug('TODO message')
        except (OSError, ValueError), err:
            logger.exception(err)
        else:
            kwargs.update({'title': title, 'track_no': track_no, 'year': year,
                           'artist': artist, 'album': album, 'genre': genre,
                           'album_artist': album_artist, 'path': path})

        super(Song, self).__init__(*args, **kwargs)


class Album(MusicBase):
    title = GObject.property(type=str)
    year = GObject.property(type=str)

    def __init__(self, song=None, *args, **kwargs):
        if song:
            kwargs.update({'title': song.album or _('Unknown album'),
                           'year': song.year})
        super(Album, self).__init__(*args, **kwargs)


class Artist(MusicBase):
    name = GObject.property(type=str)

    def __init__(self, song=None, *args, **kwargs):
        super(Artist, self).__init__(*args, **kwargs)
        if song:
            name = song.album_artist or song.artist
            self.set_property('name', name or _('Unknown artist'))

