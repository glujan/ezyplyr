#!/usr/bin/python
# -*- coding: utf8 -*-

import fnmatch
import itertools
import logging
import os
import urllib

from gi.repository import Gdk, Gtk, Gst, GObject
from gi.repository.GdkPixbuf import Pixbuf

import models
import utils
from settings import Settings
from utils import ugettext as _


logger = logging.getLogger()

RESOURCES = os.path.join(os.path.dirname(__file__), 'res')
NAME = u'EzyPlyr'
VERSION = '0.1'
SONG_INFO = 0


class Playlist(Gtk.TreeView):

    UPDATED = 'playlist-updated'

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

        self._init_signals()

    def _init_signals(self):
        self.enable_model_drag_dest([], Gdk.DragAction.COPY)
        self.drag_dest_add_uri_targets()
        self.connect('drag-data-received', self._on_drag_data_received)

        GObject.signal_new(self.UPDATED, self,
                           GObject.SIGNAL_RUN_LAST, GObject.TYPE_PYOBJECT,
                           (GObject.TYPE_PYOBJECT,))

    def _on_drag_data_received(self, widget, drag_context, x, y, data,
                               info, time):
        if info == SONG_INFO:
            model = widget.get_model()
            for uri in data.get_uris():
                s = models.Song(path=urllib.url2pathname(uri))
                model.append((s,))
            self.emit('playlist-updated', {'added': len(data.get_uris()),
                                           'position': -1})

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


class Player(GObject.GObject):

    ENDED = 'stream-ended'
    UPDATED = 'stream-updated'

    def __init__(self, **kwargs):
        super(Player, self).__init__()
        self.set_properties(**kwargs)

        Gst.init_check(None)
        self.playing = False
        self.player = None
        self.path = None

        self._init_player()
        self._init_signals()

    def _init_player(self):
        self.player = Gst.ElementFactory.make("playbin", "player")
        pulse = Gst.ElementFactory.make("pulsesink", "pulse")
        self.player.set_property("audio-sink", pulse)
        self.player.set_state(Gst.State.NULL)

    def _init_signals(self):
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)

        GObject.signal_new(self.ENDED, self, GObject.SIGNAL_RUN_LAST,
                           GObject.TYPE_PYOBJECT, (GObject.TYPE_PYOBJECT,))

        GObject.signal_new(self.UPDATED, self, GObject.SIGNAL_RUN_LAST,
                           GObject.TYPE_PYOBJECT, (GObject.TYPE_PYOBJECT,))

    def toggle_play(self, path=None):
        if self.playing:
            self.pause()
        else:
            self.play(path)

    def play(self, path=None):
        if self.path != path:
            self.path = path
            uri = 'file://' + urllib.pathname2url(path)
            self.player.set_property("uri", uri)

        self.player.set_state(Gst.State.PLAYING)
        self.playing = True
        self.update()
        GObject.timeout_add(1000, self.update)

    def pause(self):
        self.player.set_state(Gst.State.PAUSED)
        self.playing = False
        self.update()

    def stop(self):
        self.player.set_state(Gst.State.NULL)
        self.playing = False
        self.path = None

    def previous(self, path):
        self.stop()
        self.play(path)

    def next(self, path):
        self.stop()
        self.play(path)

    def on_message(self, bus, message):
        t = message.type

        if t == Gst.MessageType.EOS:
            self.stop()
            self.emit(self.ENDED, None)
        elif t == Gst.MessageType.ERROR:
            self.stop()
            err, debug = message.parse_error()
            logger.error(err, debug)

    def update(self):
        if self.playing is False:
            self.emit(self.UPDATED, {'playing': False})
            return False
        nanosecs = self.player.query_position(Gst.Format.TIME)[1]
        duration_nanosecs = self.player.query_duration(Gst.Format.TIME)[1]
        self.emit(self.UPDATED, {'position': nanosecs,
                                 'duraion': duration_nanosecs,
                                 'playing': True})
        return True


class SignalHandler(object):
    def __init__(self, window):
        self.window = window
        self.player = Player()
        self.settings = Settings()
        self.curr = 0

    def init_signals(self):
        self.window.connect("delete-event", self.on_delete)

        backward = utils.find_child(self.window, 'backward-button')
        play = utils.find_child(self.window, 'play-button')
        forward = utils.find_child(self.window, 'forward-button')

        backward.connect('clicked', self.on_backward_clicked)
        play.connect('clicked', self.on_play_clicked)
        forward.connect('clicked', self.on_stream_ended)

        self.player.connect(self.player.ENDED, self.on_stream_ended)
        self.player.connect(self.player.UPDATED, self.on_stream_updated)

        playlist = utils.find_child(self.window, 'playlist')
        playlist.connect(playlist.UPDATED, self.on_playlist_updated)

        utils.find_child(self.window, 'rescan_collection').connect(
            'activate', self.on_rescan_activated)
        utils.find_child(self.window, 'clear_playlist').connect(
            'activate', self.on_clear_activated)
        utils.find_child(self.window, 'about').connect(
            'activate', self.on_about_activated)

        shuffle = utils.find_child(self.window, 'shuffle')
        shuffle.set_active(self.settings.shuffle)
        shuffle.connect('activate', self.on_shuffle_activated)

        repeat = utils.find_child(self.window, 'repeat')
        repeat.set_active(self.settings.repeat)
        repeat.connect('activate', self.on_repeat_activated)

    def on_delete(self, source, event):
        self.window.settings.save()
        Gtk.main_quit(source, event)

    def on_stream_ended(self, widget, data=None):
        plst = utils.find_child(self.window, 'playlist').get_model()

        self.curr += 1
        if self.curr >= len(plst):
            self.curr = 0

        tree_iter = plst.get_iter_from_string(str(self.curr))
        song = plst.get_value(tree_iter, 0)
        self.player.next(song.path)

    def on_stream_updated(self, source, data):
        play = utils.find_child(self.window, 'play-button')
        if data['playing']:
            utils.set_icon(play, 'media-playback-pause')
        else:
            utils.set_icon(play, 'media-playback-start')

    def on_backward_clicked(self, widget, data=None):
        plst = utils.find_child(self.window, 'playlist').get_model()

        self.curr -= 1
        if self.curr < 0:
            self.curr = len(plst) - 1

        tree_iter = plst.get_iter_from_string(str(self.curr))
        song = plst.get_value(tree_iter, 0)
        self.player.previous(song.path)  #TODO first seconds move to begining

    def on_play_clicked(self, widget):
        plst = utils.find_child(self.window, 'playlist').get_model()

        if len(plst) == 0:
            return

        tree_iter = plst.get_iter_from_string(str(self.curr))
        song = plst.get_value(tree_iter, 0)
        self.player.toggle_play(song.path)

    def on_playlist_updated(self, source, data):  # TODO handle adding not at end
        pass

    def on_clear_activated(self, source=None):
        plst = utils.find_child(self.window, 'playlist').get_model()
        plst.clear()

    def on_rescan_activated(self, source=None):
        tree_library = utils.find_child(self.window, 'tree').get_model()

        def do_update():
            songs = []
            for root, dirnames, filenames in os.walk(self.settings.collection):
                for filename in fnmatch.filter(filenames, '*.mp3'):
                    path = os.path.join(root, filename).decode('utf8')
                    songs.append(models.Song(path))
            return songs

        def callback(result=None):
            def add_iter(obj, path=None):
                parent = tree_library.get_iter(path) if path else None
                it = tree_library.append(parent, (obj,))
                return tree_library.get_string_from_iter(it)

            tree_library.clear()
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

    def on_repeat_activated(self, source):
        self.settings.repeat = source.get_active()

    def on_shuffle_activated(self, source):
        self.settings.shuffle = source.get_active()

    def on_about_activated(self, source):
        about = Gtk.AboutDialog(
            self, program_name=NAME, version=VERSION, modal=True,
            website=u'http://example.org/', website_label=_('Website'),
            comments=_("Music player created using Python and GTK3"),
            transient_for=self.window, can_focus=False
        )

        icon_path = os.path.join(RESOURCES, 'icon32.ico')
        about.set_logo(Pixbuf.new_from_file_at_size(icon_path, 32, 32))
        about.set_authors([u"Grzegorz Janik"])

        about.run()
        about.destroy()


class MusicWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title=NAME)

        self.plst = Gtk.ListStore(models.Song)
        self.tree_library = Gtk.TreeStore(models.MusicBase)

        self.scale = Gtk.HScale(adjustment=Gtk.Adjustment(), draw_value=False)
        self.title = Gtk.Label('Welcome to {}!'.format(NAME))
        self.curr_time = Gtk.Label('00:00')
        self.play_pause = Gtk.Button()

        self.settings = Settings()
        self._init_gui()

        handler = SignalHandler(self)
        handler.init_signals()

        self.show_all()

    def _init_gui(self):
        self.set_border_width(3)
        self.set_default_size(800, 400)
        self.set_icon(Pixbuf.new_from_file(os.path.join(RESOURCES, 'icon.ico')))

        play_box = self._create_play_box()
        settings_box = self._create_settings_box()
        custom_title = self._create_custom_title()

        title_bar = Gtk.HeaderBar()
        title_bar.props.show_close_button = True
        title_bar.pack_start(play_box)
        title_bar.pack_end(settings_box)
        title_bar.set_custom_title(custom_title)
        self.set_titlebar(title_bar)

        list_view = Playlist(model=self.plst, name='playlist')
        tree_view = SongsTree(model=self.tree_library, name='tree')

        scrolled_tree = Gtk.ScrolledWindow()
        scrolled_tree.add(tree_view)
        scrolled_list = Gtk.ScrolledWindow()
        scrolled_list.add(list_view)

        paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        paned.set_position(200)
        paned.add1(scrolled_tree)
        paned.add2(scrolled_list)
        self.add(paned)

    def _create_custom_title(self):  # TODO: Update on song (title,current_time)
        scale_wrap = Gtk.VBox(spacing=3)
        scale_wrap.set_size_request(400, 20)
        scale_wrap.pack_start(self.title, True, True, 5)

        scale_box = Gtk.HBox(spacing=3)
        scale_box.pack_start(self.curr_time, False, False, 8)
        scale_box.pack_start(self.scale, True, True, 0)
        scale_wrap.pack_start(scale_box, True, True, 0)

        return scale_wrap

    def _create_play_box(self):
        play_box = Gtk.HBox()
        Gtk.StyleContext.add_class(play_box.get_style_context(), "linked")

        backward = Gtk.Button(name='backward-button')
        utils.set_icon(backward, 'media-skip-backward')
        play_box.add(backward)

        self.play_pause.set_name('play-button')
        utils.set_icon(self.play_pause, 'media-playback-start')
        play_box.add(self.play_pause)

        forward = Gtk.Button(name='forward-button')
        utils.set_icon(forward, 'media-skip-forward')
        play_box.add(forward)

        return play_box

    def _create_settings_box(self):
        menu = Gtk.Menu()
        menu.set_halign(Gtk.Align.CENTER)

        button = Gtk.MenuButton(popup=menu)
        utils.set_icon(button, "emblem-system")

        items = ((Gtk.CheckMenuItem(_('Shuffle')), 'shuffle'),
                 (Gtk.CheckMenuItem(_('Repeat')), 'repeat'),
                 (Gtk.SeparatorMenuItem(), None),
                 (Gtk.MenuItem(_('Rescan collection')), 'rescan_collection'),
                 (Gtk.MenuItem(_('Clear playlist')), 'clear_playlist'),
                 (Gtk.SeparatorMenuItem(), None),
                 (Gtk.MenuItem(_('About')), 'about'))

        for item, name in items:
            if name:
                item.set_name(name)
            item.show()
            menu.append(item)

        return button
