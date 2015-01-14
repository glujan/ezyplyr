# -*- coding: utf-8 -*-

import gettext
import threading

from gi.repository import Gtk, GObject, Gio, Notify


t = gettext.translation('musicx', 'locale', fallback=True)
ugettext = t.ugettext


def add_icon(button, icon_name, size=None):
    if not size:
        size = Gtk.IconSize.LARGE_TOOLBAR
    icon = Gio.ThemedIcon(name=icon_name)
    image = Gtk.Image.new_from_gicon(icon, size)
    button.add(image)


def sort_func(model, row1, row2, user_data):
    value1 = model.get_value(row1, 0)
    value2 = model.get_value(row2, 0)
    if value1 and value2:
        sort = cmp(value1, value2)
    else:
        sort = -1
    return sort


class LazyDict(dict):
    def setdefault(self, key, default=None):
        return self[key] if key in self else dict.setdefault(
            self, key, default()
        )
