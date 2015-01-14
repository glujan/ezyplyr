#!/usr/bin/python
# -*- coding: utf8 -*-

import fnmatch
import itertools
import logging
import urllib
import os

from gi.repository import Gdk, Gtk
from gi.repository.GdkPixbuf import Pixbuf

import models
import utils
from settings import Settings
from utils import ugettext as _


logger = logging.getLogger()

RESOURCES = os.path.join(os.path.dirname(__file__), 'res')
NAME = u'MusicX'
VERSION = '0.1'
SONG_INFO = 0


class Playlist(Gtk.TreeView):
    def __init__(self, *args, **kwargs):
        super(Gtk.TreeView, self).__init__(*args, **kwargs)

        columns = ((u'#', 'track_no'),
                   (_('Title'), 'title'),
                   (_('Artist'), 'artist'),
                   (_('Album'), 'album'),
                   (_('Year'), 'year'))

        cell = Gtk.CellRendererText()

        self.set_search_column(1)
        self.set_enable_search(True)

        selection = self.get_selection()
        selection.set_mode(Gtk.SelectionMode.MULTIPLE)

        for title, attr in columns:
            column = Gtk.TreeViewColumn(title=title)
            column.set_name(attr)
            column.pack_start(cell, True)
            column.set_cell_data_func(cell, self._cell_data_func, attr)
            column.set_resizable(True)
            column.set_min_width(50)
            # column.set_fixed_width(80)
            self.append_column(column)

        self.enable_model_drag_dest([], Gdk.DragAction.COPY)
        self.drag_dest_add_uri_targets()
        self.connect('drag-data-received', self._on_drag_data_received)

    def _on_drag_data_received(self, widget, drag_context, x, y, data,
                               info, time):
        if info == SONG_INFO:
            model = widget.get_model()
            for uri in data.get_uris():
                s = models.Song(path=urllib.url2pathname(uri))
                model.append((s,))

    def _cell_data_func(self, column, cell, model, iter, data):
        item = model.get_value(iter, 0)
        value = getattr(item, column.get_name(), '')
        cell.set_property('text', str(value or '').decode('utf8'))


class SongsTree(Gtk.TreeView):
    def __init__(self, *args, **kwargs):
        super(SongsTree, self).__init__(*args, **kwargs)

        self.set_search_column(0)
        self.set_enable_search(True)
        self.set_enable_tree_lines(True)

        self.get_model().set_sort_func(0, utils.sort_func, None)
        self.get_model().set_sort_column_id(0, Gtk.SortType.ASCENDING)
        self.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)

        cell = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(title=_("Collection"))
        column.pack_start(cell, True)
        column.set_cell_data_func(cell, self._cell_data_func)
        self.append_column(column)

        self.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK,
                                      [], Gdk.DragAction.COPY)
        self.drag_source_add_uri_targets()
        self.connect('drag-data-get', self._on_drag_data_get)

    def _on_drag_data_get(self, widget, drag_context, data, info, time):
        if info == SONG_INFO:
            selection = self.get_selection()
            tree_store, tree_paths = selection.get_selected_rows()
            songs = (self._retrieve_songs(tp.copy()) for tp in tree_paths)
            songs = list(itertools.chain(*songs))
            data.set_uris(songs)

    def get_model_value(self, tree_path):
        song = None
        try:
            tree_iter = self.get_model().get_iter(tree_path)
            song = self.get_model().get_value(tree_iter, 0)
        except ValueError:
            pass

        return song

    def _retrieve_songs(self, tree_path):
        level = tree_path.get_depth()
        items = []

        if level == 3:
            song = self.get_model_value(tree_path)
            if song:
                items.append(urllib.pathname2url(song.path))
                tree_path.up()
        elif level < 3:
            tree_path.down()
            to_extend = self._retrieve_songs(tree_path.copy())
            while to_extend:
                items.extend(to_extend)
                tree_path.next()
                to_extend = self._retrieve_songs(tree_path.copy())

        return items

    def _cell_data_func(self, column, cell, model, iter, data):
        item = model.get_value(iter, 0)
        cell.set_property('text', unicode(item))


class MusicWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title=NAME)

        self.plst = Gtk.ListStore(models.Song)
        self.tree_library = Gtk.TreeStore(models.MusicBase)

        self.scale = Gtk.HScale(adjustment=Gtk.Adjustment(), draw_value=False)
        self.title = Gtk.Label('Welcome to {}!'.format(NAME))
        self.curr_time = Gtk.Label('00:00')

        self.settings = Settings()
        self.shuffle_menu = Gtk.CheckMenuItem(_('Shuffle'))
        self.repeat_menu = Gtk.CheckMenuItem(_('Repeat'))
        self.group_menu = Gtk.CheckMenuItem(_('Group by Album artist'))

        self._init_gui()
        self.show_all()

    def _init_gui(self):
        self.set_border_width(3)
        self.set_default_size(800, 400)
        self.set_icon(Pixbuf.new_from_file(os.path.join(RESOURCES, 'icon.ico')))
        self.connect("delete-event", self.quit)

        play_box = self._create_play_box()
        settings_box = self._create_settings_box()
        custom_title = self._create_custom_title()

        title_bar = Gtk.HeaderBar()
        title_bar.props.show_close_button = True
        title_bar.pack_start(play_box)
        title_bar.pack_end(settings_box)
        title_bar.set_custom_title(custom_title)
        self.set_titlebar(title_bar)

        list_view = Playlist(model=self.plst)
        tree_view = SongsTree(model=self.tree_library)

        scrolled_tree = Gtk.ScrolledWindow()
        scrolled_tree.add(tree_view)
        scrolled_list = Gtk.ScrolledWindow()
        scrolled_list.add(list_view)

        paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        paned.set_position(200)
        paned.add1(scrolled_tree)
        paned.add2(scrolled_list)
        self.add(paned)

    def clear_playlist(self, source=None):
        self.plst.clear()

    def rescan_collection(self, source=None):
        def do_update():
            songs = []
            for root, dirnames, filenames in os.walk(self.settings.collection):
                for filename in fnmatch.filter(filenames, '*.mp3'):
                    path = os.path.join(root, filename).decode('utf8')
                    songs.append(models.Song(path))
            return songs

        def callback(result=None):
            def add_iter(obj, path=None):
                parent = self.tree_library.get_iter(path) if path else None
                it = self.tree_library.append(parent, (obj,))
                return self.tree_library.get_string_from_iter(it)

            self.tree_library.clear()
            artists = utils.LazyDict()
            albums = utils.LazyDict()

            for song in result:
                artist = models.Artist(song)
                album = models.Album(song)

                path = artists.setdefault(artist, lambda: add_iter(artist))
                path = albums.setdefault(album, lambda: add_iter(album, path))

                add_iter(song, path)

            if source:
                utils.notify(_('Collection scanned!'))

        def errback(error):
            logger.exception(error)
            utils.notify(_('Error scanning collection'), 'dialog-error')

        utils.async_call(do_update, callback, errback)

    def quit(self, source, event):
        self.settings.save()
        Gtk.main_quit(source, event)

    def _show_about(self, widget):
        about = Gtk.AboutDialog(
            self, program_name=NAME, version=VERSION, modal=True,
            website=u'http://example.org/', website_label=_('Website'),
            comments=_("Music player created using Python and GTK3"),
            transient_for=self, can_focus=False
        )

        icon_path = os.path.join(RESOURCES, 'icon32.ico')
        about.set_logo(Pixbuf.new_from_file_at_size(icon_path, 32, 32))
        about.set_authors([u"Grzegorz Janik"])

        about.run()
        about.destroy()

    def _create_custom_title(self):  # TODO: Update on song (title,current_time)
        scale_wrap = Gtk.VBox(spacing=3)
        scale_wrap.set_size_request(400, 20)
        scale_wrap.pack_start(self.title, True, True, 5)

        scale_box = Gtk.HBox(spacing=3)
        scale_box.pack_start(self.curr_time, False, False, 8)
        scale_box.pack_start(self.scale, True, True, 0)
        scale_wrap.pack_start(scale_box, True, True, 0)

        return scale_wrap

    def _create_play_box(self):  # TODO: Attach signals
        play_box = Gtk.HBox()
        Gtk.StyleContext.add_class(play_box.get_style_context(), "linked")

        button = Gtk.Button()
        utils.add_icon(button, 'media-skip-backward')
        play_box.add(button)

        button = Gtk.Button()
        utils.add_icon(button, 'media-playback-start')
        play_box.add(button)

        button = Gtk.Button()
        utils.add_icon(button, 'media-skip-forward')
        play_box.add(button)

        return play_box

    def _create_settings_box(self):
        menu = Gtk.Menu()
        menu.set_halign(Gtk.Align.CENTER)

        button = Gtk.MenuButton(popup=menu)
        utils.add_icon(button, "emblem-system")

        items = ((self.shuffle_menu, self._toggle_shuffle),
                 (self.repeat_menu, self._toggle_repeat),
                 (Gtk.SeparatorMenuItem(), None),
                 (Gtk.MenuItem(_('Rescan collection')), self.rescan_collection),
                 (Gtk.MenuItem(_('Clear playlist')), self.clear_playlist),
                 (Gtk.SeparatorMenuItem(), None),
                 (Gtk.MenuItem(_('About')), self._show_about))

        for item, action in items:
            if action:
                item.connect('activate', action)
            item.show()
            menu.append(item)

        self.shuffle_menu.set_active(self.settings.shuffle)
        self.repeat_menu.set_active(self.settings.repeat)

        return button

    def _toggle_repeat(self, source):
        self.settings.repeat = source.get_active()

    def _toggle_shuffle(self, source):
        self.settings.shuffle = source.get_active()
