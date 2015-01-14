#!/usr/bin/python
# -*- coding: utf8 -*-


from gi import require_version
from gi.repository import Gtk, Notify

from gui import MusicWindow, NAME

require_version('Gst', '1.0')


if __name__ == '__main__':
    import locale
    import logging

    locale.setlocale(locale.LC_ALL, '')
    logging.basicConfig()

    Notify.init(NAME)
    app = MusicWindow()
    Gtk.main()