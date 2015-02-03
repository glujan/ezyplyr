#!/usr/bin/python
# -*- coding: utf8 -*-


from gi import require_version
from gi.repository import Gst, Gtk, Notify

from gui import EzyWindow, NAME

require_version('Gst', '1.0')


if __name__ == '__main__':
    import locale
    import logging

    locale.setlocale(locale.LC_ALL, '')
    logging.basicConfig()

    Notify.init(NAME)
    Gst.init(None)
    app = EzyWindow()
    Gtk.main()
