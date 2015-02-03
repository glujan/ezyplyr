# -*- coding: utf-8 -*-

from __future__ import division, unicode_literals

import gettext
import threading

from gi.repository import Gtk, GObject, Gio, Notify


t = gettext.translation('ezyplyr', 'locale', fallback=True)
ugettext = t.ugettext


def find_child(parent, name):
    if parent.get_name() == name:
        return parent

    if isinstance(parent, Gtk.MenuButton):
        for child in parent.get_popup().get_children():
            ret = find_child(child, name)
            if ret:
                return ret

    if isinstance(parent, Gtk.Container):
        for child in parent.get_children():
            ret = find_child(child, name)
            if ret:
                return ret
    return None


def set_icon(button, icon_name, size=None):
    if not size:
        size = Gtk.IconSize.LARGE_TOOLBAR
    icon = Gio.ThemedIcon(name=icon_name)
    image = Gtk.Image.new_from_gicon(icon, size)
    button.set_image(image)


def get_time(seconds):
    minutes = seconds // 60
    seconds -= minutes * 60
    return '{:02}:{:02}'.format(minutes, seconds)


def sort_func(model, row1, row2, user_data):
    value1 = model.get_value(row1, 0)
    value2 = model.get_value(row2, 0)
    if value1 and value2:
        sort = cmp(value1, value2)
    else:
        sort = -1
    return sort


def async_call(func, callback=None, errback=None, *args, **kwargs):
    def no_action(*args, **kwargs):
        pass

    if not callback:
        callback = no_action
    if not errback:
        errback = no_action

    def do_call():
        try:
            result = func(*args, **kwargs)
        except Exception, err:
            GObject.idle_add(lambda: errback(err))
        else:
            GObject.idle_add(lambda: callback(result))

    thread = threading.Thread(target=do_call)
    thread.start()


def notify(message, message_type=None):
    if not message_type:
        message_type = 'dialog-information'
    app = Notify.get_app_name()
    popup = Notify.Notification.new(app, message, message_type)
    popup.show()


class LazyDict(dict):
    def setdefault(self, key, default=None):
        return self[key] if key in self else dict.setdefault(
            self, key, default()
        )
