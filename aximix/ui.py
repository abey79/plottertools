"""
Strategy:

- use mido
- use asyncio urwid
- https://stackoverflow.com/questions/56277440/how-can-i-integrate-python-mido-and-asyncio
"""

import asyncio
from typing import Any

import urwid
from axy.axidraw import axy
from axy.stub import set_print_callback
from watchgod import awatch

from .color_defs import GREEN, ORANGE, PURPLE, RED
from .file_selector import FILE_SELECTOR_PALETTE, FileSelector
from .launchpad import Checkbox, Fader, Launchpad, Selector
from .pagelayout import PageLayout
from .settings import PersistentVar, get_axidraw_config, get_setting

CONFIG_SETTINGS = {
    "pen_rate_lower": ("Pen rate lower:", 50),
    "pen_rate_raise": ("Pen rate raise:", 75),
    "pen_delay_down": ("Pen delay down (ms):", 0),
    "pen_delay_up": ("Pen delay up (ms)", 0),
    "accel": ("Acceleration", (1, 100), 75),
    "model": ("Axidraw model", 2),
    "port": ("Port", ""),
}

PALETTE = [
    ("progress", "black", "white"),
    ("progress_completed", "white", "black"),
    ("page_format", "white,bold", "dark green"),
    ("landscape", "white,bold", "dark red"),
    ("portrait", "dark red,bold", "light gray"),
    ("upright", "dark blue,bold", "light gray"),
    ("rotate", "white,bold", "dark blue"),
    ("no_center", "dark green,bold", "light gray"),
    ("center", "white,bold", "dark green"),
    ("no_fit", "dark magenta,bold", "light gray"),
    ("fit", "white,bold", "dark magenta"),
]
PALETTE += FILE_SELECTOR_PALETTE


class PersistentFader(Fader):
    def __init__(self, name: str, default: Any, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._persistent_var = PersistentVar(name, default)
        self.value = self._persistent_var.value
        self.on_value_changed.connect(lambda val: self._persistent_var.set_value(val))


class PersistentSelector(Selector):
    def __init__(self, name: str, default: Any, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._persistent_var = PersistentVar(name, default)
        self.value = self._persistent_var.value
        self.on_value_change.connect(self._persistent_var.set_value)

    def make_widget(self, label, attr=""):
        label_txt = urwid.Text(f"{label}: ")
        value_txt = urwid.Text(self.value)
        self.on_value_change.connect(value_txt.set_text)
        return urwid.Padding(
            urwid.AttrMap(
                urwid.Columns(
                    [
                        ("pack", label_txt),
                        (max(len(s) for s in self._values), value_txt),
                    ]
                ),
                attr,
            ),
            align="left",
        )


class PersistentCheckbox(Checkbox):
    def __init__(self, name: str, default: bool, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._persistent_var = PersistentVar(name, default)
        self.value = self._persistent_var.value
        self.on_value_change.connect(self._persistent_var.set_value)

    def make_widget(self, label_on, label_off, attr_on="", attr_off=""):
        txt = urwid.Text("")
        attrmap = urwid.AttrMap(txt, "")

        def update(val):
            txt.set_text(label_on if val else label_off)
            attrmap.attr_map = {None: attr_on if val else attr_off}

        update(self.value)
        self.on_value_change.connect(update)
        return attrmap


def main():
    aloop = asyncio.get_event_loop()
    lp = Launchpad(aloop, get_setting("input_port"), get_setting("output_port"))
    pl = PageLayout()

    page_format_selector = PersistentSelector(
        "page_format",
        "a4",
        lp,
        ["a6", "a5", "a4", "a3", "letter", "legal", "tabloid"],
        12,
        11,
        GREEN,
        GREEN,
    )

    landscape_check = PersistentCheckbox("landscape", False, lp, 13, 5, 0)
    rotate_check = PersistentCheckbox("rotate", False, lp, 14, 45, 0)
    center_check = PersistentCheckbox("center", True, lp, 15, 21, 0)
    fit_to_page_check = PersistentCheckbox("fit_to_page", False, lp, 16, 53, 0)

    landscape_check.on_value_change.connect(lambda val: setattr(pl, "landscape", val))
    rotate_check.on_value_change.connect(lambda val: setattr(pl, "rotate", val))
    center_check.on_value_change.connect(lambda val: setattr(pl, "center", val))
    fit_to_page_check.on_value_change.connect(
        lambda val: setattr(pl, "fit_to_page", val)
    )

    margin_selector = PersistentSelector(
        "margin", "20mm", lp, [f"{i}mm" for i in range(0, 105, 5)], 18, 17, GREEN, GREEN
    )
    margin_selector.on_value_change.connect(lambda val: setattr(pl, "margin", val))

    pl.page_format = page_format_selector.value
    pl.landscape = landscape_check.value
    pl.rotate = rotate_check.value
    pl.center = center_check.value
    pl.fit_to_page = fit_to_page_check.value
    pl.margin = margin_selector.value

    txt = urwid.Text("")
    txt2 = urwid.Text("")
    txt3 = urwid.Text("")
    txt4 = urwid.Text("")
    page_layout = urwid.Padding(
        urwid.Columns(
            [
                page_format_selector.make_widget("Format", "page_format"),
                landscape_check.make_widget(
                    "Landscape", "Portrait", "landscape", "portrait"
                ),
                rotate_check.make_widget(
                    "Rotate: ON", "Rotate: OFF", "rotate", "upright"
                ),
                center_check.make_widget(
                    "Center: ON", "Center: OFF", "center", "no_center"
                ),
                fit_to_page_check.make_widget("Fit: ON", "Fit: OFF", "fit", "no_fit"),
                margin_selector.make_widget("Margin", "page_format"),
            ],
            dividechars=1,
        )
    )
    fill = urwid.Filler(
        urwid.Pile([txt, txt2, txt3, txt4, page_layout]),
        "top",
    )

    def axy_print(s):
        txt2.set_text(s)

    # init axy
    set_print_callback(axy_print)
    for k, v in get_axidraw_config().items():
        axy.set_option(k, v)

    async def watch_svg():
        async for changes in awatch(get_setting("svg_dir")):
            txt4.set_text(str(changes))

    def print_event(msg):
        txt.set_text(str(msg))

    # noinspection PyUnusedLocal
    def exit_to_shell():
        axy.shutdown()
        raise urwid.ExitMainLoop()

    def shutdown():
        axy.shutdown()

    def print_value(value):
        txt3.set_text(str(value))

    # noinspection PyUnusedLocal
    def select_file(path):
        txt4.set_text(path)

    loop = urwid.MainLoop(
        fill, palette=PALETTE, event_loop=urwid.AsyncioEventLoop(loop=aloop)
    )
    aloop.create_task(watch_svg())

    # setup file selector
    file_selector = FileSelector(loop, lp, get_setting("svg_dir"))
    file_selector.on_accept.connect(select_file)
    file_selector.on_accept.connect(lambda path: setattr(pl, "path", path))

    # setup HW UX
    pen_up_fader = PersistentFader(
        "pen_up_pos",
        60,
        lp,
        68,
        61,
        list(range(62, 68)),
        min_value=20,
        max_value=80,
    )
    pen_up_fader.on_value_changed.connect(print_value)
    axy.set_option("pen_pos_up", pen_up_fader.value)
    pen_up_fader.on_value_changed.connect(lambda val: axy.set_option("pen_pos_up", val))

    pen_down_fader = PersistentFader(
        "pen_down_pos",
        45,
        lp,
        58,
        51,
        list(range(52, 58)),
        min_value=20,
        max_value=80,
    )
    pen_down_fader.on_value_changed.connect(print_value)
    axy.set_option("pen_pos_down", pen_down_fader.value)
    pen_down_fader.on_value_changed.connect(
        lambda val: axy.set_option("pen_pos_down", val)
    )

    speed_pendown_fader = PersistentFader(
        "speed_pendown",
        25,
        lp,
        48,
        41,
        list(range(42, 48)),
        min_value=10,
        max_value=100,
    )
    speed_pendown_fader.on_value_changed.connect(print_value)
    axy.set_option("speed_pendown", speed_pendown_fader.value)
    speed_pendown_fader.on_value_changed.connect(
        lambda val: axy.set_option("speed_pendown", val)
    )

    accel_fader = PersistentFader(
        "accel",
        75,
        lp,
        38,
        31,
        list(range(32, 38)),
        min_value=1,
        max_value=100,
    )
    accel_fader.on_value_changed.connect(print_value)
    axy.set_option("accel", accel_fader.value)
    accel_fader.on_value_changed.connect(lambda val: axy.set_option("accel", val))

    lp.on_raw_event.connect(print_event)

    lp.set_key_color(69, PURPLE)
    lp.on_key_press(69).connect(lambda key: axy.pen_up())
    lp.set_key_color(59, PURPLE)
    lp.on_key_press(59).connect(lambda key: axy.pen_down())

    lp.set_key_color(98, GREEN, mode="pulse")
    lp.on_key_press(98).connect(lambda key: axy.plot_svg(pl.get_plot_svg()))

    lp.set_key_color(19, RED, mode="solid")
    lp.on_key_press(19).connect(lambda key: exit_to_shell())

    # use drum key for power off
    lp.set_key_color(96, ORANGE)
    lp.on_key_press(96).connect(lambda key: shutdown())

    # use session key for file select
    lp.set_key_color(95, PURPLE)
    lp.on_key_press(95).connect(lambda key: file_selector.show())

    # use Keys key for preview
    lp.set_key_color(97, GREEN)
    lp.on_key_press(97).connect(lambda key: pl.preview())

    loop.run()
    lp.clear_all()
