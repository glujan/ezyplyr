#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import subprocess

from ConfigParser import SafeConfigParser


SETTINGS_FILE = os.path.expanduser('~/.config/ezyplyr/ezyplyr.rc')


class Settings(object):

    def __init__(self):
        super(Settings, self).__init__()
        self.config = SafeConfigParser()

        if os.path.isfile(SETTINGS_FILE):
            self.config.read(SETTINGS_FILE)
        else:
            try:
                DEFAULT_DIR = subprocess.check_output(['xdg-user-dir', 'MUSIC'])
            except OSError:
                DEFAULT_DIR = os.path.expanduser('~')
            self.config.add_section('Playback')
            self.config.set('Playback', 'repeat', 'True')
            self.config.set('Playback', 'shuffle', 'True')
            self.config.add_section('Collection')
            self.config.set('Collection', 'dir', DEFAULT_DIR.strip())

    def save(self):
        settings_dir = os.path.dirname(SETTINGS_FILE)
        if not os.path.isdir(settings_dir):
            os.makedirs(settings_dir)

        with open(SETTINGS_FILE, 'wb') as configfile:
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
