#!/usr/bin/python
# -*- coding: utf8 -*-

from __future__ import absolute_import
from builtins import str
from builtins import object

import fnmatch
import os

from ConfigParser import SafeConfigParser

from gi.repository import GLib

from .models import Song


class Settings(object):
    SETTINGS_FILE = os.path.join(GLib.get_user_config_dir(), 'ezyplyr', 'ezyplyr.rc')
    COLLECTION_FILE = os.path.join(GLib.get_user_data_dir(), 'ezyplyr', 'collection.csv')

    def __init__(self):
        super(Settings, self).__init__()
        self.config = SafeConfigParser()

        if os.path.isfile(self.SETTINGS_FILE):
            self.config.read(self.SETTINGS_FILE)
        else:
            try:
                DEFAULT_DIR = GLib.get_user_special_dir(GLib.USER_DIRECTORY_MUSIC)
            except OSError:
                DEFAULT_DIR = os.path.expanduser('~/Music')
            self.config.add_section('Playback')
            self.config.set('Playback', 'repeat', 'True')
            self.config.set('Playback', 'shuffle', 'True')
            self.config.add_section('Collection')
            self.config.set('Collection', 'dir', DEFAULT_DIR.strip())

    def save(self):
        settings_dir = os.path.dirname(self.SETTINGS_FILE)
        if not os.path.isdir(settings_dir):
            os.makedirs(settings_dir)

        with open(self.SETTINGS_FILE, 'wb') as configfile:
            self.config.write(configfile)

    def rescan_collection(self):
        songs = []
        for root, dirnames, filenames in os.walk(self.collection):
            for filename in fnmatch.filter(filenames, '*.mp3'):
                path = os.path.join(root, filename).decode('utf8')
                songs.append(Song(path))
        return songs

    def _getrepeat(self):
        return self.config.getboolean('Playback', 'repeat')

    def _setrepeat(self, value):
        self.config.set('Playback', 'repeat', str(value))

    repeat = property(_getrepeat, _setrepeat)

    def _getshuffle(self):
        return self.config.getboolean('Playback', 'shuffle')

    def _setshuffle(self, value):
        self.config.set('Playback', 'shuffle', str(value))

    shuffle = property(_getshuffle, _setshuffle)

    def _getdir(self):
        return self.config.get('Collection', 'dir')

    def _setdir(self, value):
        self.config.set('Collection', 'dir', value)

    collection = property(_getdir, _setdir)
