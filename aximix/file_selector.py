import asyncio
import math
import os
from pathlib import Path
from typing import List, Optional

import urwid
from watchgod import Change, awatch

from .color_defs import RED
from .launchpad import Launchpad, Scene
from .signal import Signal

FILE_SELECTOR_PALETTE = [
    ("file0", "white,bold", "dark blue"),
    ("file1", "white,bold", "dark red"),
    ("file2", "white,bold", "dark green"),
    ("file3", "white,bold", "dark magenta"),
]


def _make_square(a):
    return [a, a + 1, a - 10, a - 9]


class FileSelector:
    LAYOUT_DEF = {
        (0, 0): ("file0", _make_square(81), 45),
        (0, 1): ("file1", _make_square(83), 5),
        (1, 0): ("file1", _make_square(61), 5),
        (1, 1): ("file0", _make_square(63), 45),
        (0, 2): ("file2", _make_square(85), 21),
        (0, 3): ("file3", _make_square(87), 53),
        (1, 2): ("file3", _make_square(65), 53),
        (1, 3): ("file2", _make_square(67), 21),
        (2, 0): ("file2", _make_square(41), 21),
        (2, 1): ("file3", _make_square(43), 53),
        (3, 0): ("file3", _make_square(21), 53),
        (3, 1): ("file2", _make_square(23), 21),
        (2, 2): ("file0", _make_square(45), 45),
        (2, 3): ("file1", _make_square(47), 5),
        (3, 2): ("file1", _make_square(25), 5),
        (3, 3): ("file0", _make_square(27), 45),
    }

    def __init__(self, loop, launchpad: Launchpad, svg_dir: str):
        self.on_accept = Signal()

        self._loop = loop
        self._lp = launchpad
        self._dir = svg_dir
        self._scene = Scene(launchpad)
        self._old_widget: Optional[urwid.Widget] = None
        self._file_list: List[str] = []

        self._pile_of_cols = urwid.Pile([])
        self._overlay_widget = urwid.Overlay(
            urwid.Filler(urwid.LineBox(self._pile_of_cols, "Choose a file...")),
            self._loop.widget,
            align="center",
            width=("relative", 80),
            valign="middle",
            height=9,
        )
        self._columns = 4
        self._rows = 4

        # setup file list
        for path in sorted(
            Path(self._dir).iterdir(), key=os.path.getmtime, reverse=True
        ):
            if path.is_file() and path.name.lower().endswith(".svg"):
                self._file_list.append(str(path))
        self._update_path_list()
        asyncio.get_event_loop().create_task(self._process_dir_change(self._dir))

        # setup scene
        self._scene.set_key_color(19, RED)
        self._scene.on_key_press(19).connect(lambda key: self.hide())

    async def _process_dir_change(self, dirpath: str):
        async for changes in awatch(dirpath):
            for change, path in changes:
                if not path.lower().endswith(".svg"):
                    continue

                if change == Change.added:
                    self._file_list.insert(0, path)
                elif change == Change.modified:
                    try:
                        idx = self._file_list.index(path)
                    except ValueError:
                        self._file_list.insert(0, path)
                    else:
                        self._file_list.insert(0, self._file_list.pop(idx))
                elif change == Change.deleted:
                    try:
                        self._file_list.remove(path)
                    except ValueError:
                        pass
            self._update_path_list()

    def _update_path_list(self):
        cnt = len(self._file_list)
        row_cnt = min(math.ceil(cnt / self._columns), 4)

        contents = []
        for row in range(row_cnt):
            files = self._file_list[(row * self._columns) : ((row + 1) * self._columns)]
            column_widgets = [
                urwid.AttrMap(
                    urwid.Text(f.lstrip(self._dir), wrap="ellipsis"),
                    self.LAYOUT_DEF[(row, col)][0],
                )
                for col, f in enumerate(files)
            ]
            # pad columns to the total count
            column_widgets += [urwid.Text("")] * (self._columns - len(column_widgets))

            def make_callback(f):
                return lambda k: self.accept(f)

            # setup key colors
            for col, f in enumerate(files):
                color = self.LAYOUT_DEF[(row, col)][2]
                for key in self.LAYOUT_DEF[(row, col)][1]:
                    self._scene.set_key_color(key, color)
                    self._scene.on_key_press(key).connect(make_callback(f))
            for col in range(len(files), self._columns):
                for key in self.LAYOUT_DEF[(row, col)][1]:
                    self._scene.set_key_color(key, 0)

            contents.append(
                (
                    urwid.Columns(column_widgets, dividechars=2),
                    ("weight", 1),
                )
            )

            if row < (row_cnt - 1):
                contents.append((urwid.Text(""), ("weight", 1)))
        self._pile_of_cols.contents = contents

        # clear unused row's of LED
        for row in range(row_cnt, self._rows):
            for col in range(self._columns):
                for key in self.LAYOUT_DEF[(row, col)][1]:
                    self._scene.set_key_color(key, 0)

    def show(self):
        self._lp.push_scene(self._scene)
        self._old_widget = self._loop.widget
        self._loop.widget = self._overlay_widget

    def hide(self):
        self._loop.widget = self._old_widget
        self._lp.pop_scene()

    def accept(self, path: str):
        self.hide()
        self.on_accept(path)
