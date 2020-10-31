import asyncio
import logging
import math
from typing import Dict, Iterable, List, Optional, Tuple, TypeVar, Union

import attr
import mido

from .signal import Signal

ALL_KEYS = list(key for key in range(11, 99) if key % 10 != 0)
SET_LED_PREAMBLE = [0, 32, 41, 2, 13, 3]


def _make_stream(loop):
    queue = asyncio.Queue()

    def callback(message):
        loop.call_soon_threadsafe(queue.put_nowait, message)

    async def stream():
        while True:
            yield await queue.get()

    return callback, stream()


@attr.s(auto_attribs=True)
class _LEDState:
    key: int
    mode: int
    data: List[int]

    def encode(self) -> List[int]:
        return [self.mode, self.key, *self.data]


class Scene:
    def __init__(self, launchpad: "Launchpad"):
        self._lp = launchpad
        self._map: Dict[int, _LEDState] = {}
        self._active = False
        self._on_key_press = {}

        self.clear_all()

    def on_key_press(self, key: int):
        return self._on_key_press.setdefault(key, Signal())

    def activate(self) -> None:
        self._active = True
        self._update_all()

    def trigger_on_key_press(self, key: int):
        """used by launchpad"""
        if key in self._on_key_press:
            self._on_key_press[key](key)

    def deactivate(self) -> None:
        self._active = False

    def clear_all(self) -> None:
        for key in ALL_KEYS:
            self._map[key] = _LEDState(key, 0, [0])

        self._update_all()

    def set_key_color(
        self,
        key: int,
        a: int,
        b: Optional[int] = None,
        c: Optional[int] = None,
        *,
        mode: Optional[str] = None,
    ) -> None:
        if key not in ALL_KEYS:
            logging.warning(f"key {key} invalid")
            return

        if c is not None:
            # RGB mode
            if mode is not None and mode != "solid":
                logging.warning(
                    f"mode {mode} unsupported with RGB input, reverting to 'solid'"
                )

            mode = 3
            data = [a, b, c]
        elif b is not None:
            # alternating mode
            if mode is not None and mode != "alternate":
                logging.warning(
                    f"mode {mode} unsupported with two color indices, reverting to 'alternate'"
                )
            mode = 1
            data = [a, b]
        else:
            if mode is None or mode == "solid":
                mode = 0
                data = [a]
            elif mode == "blink":
                mode = 1
                data = [a, 0]
            elif mode == "pulse":
                mode = 2
                data = [a]
            else:
                mode = 0
                data = [a]
                logging.warning(
                    f"mode {mode} unsupported with one color index, reverting to 'solid'"
                )

        state = _LEDState(key, mode, data)
        self._map[key] = state
        self._update([state])

    def set_keys_color(self, colors: List[Tuple[int, int, int, int]]) -> None:
        to_update = []
        for key, r, g, b in colors:
            if key in ALL_KEYS:
                state = _LEDState(key, 3, [r, g, b])
                to_update.append(state)
                self._map[key] = state
            else:
                logging.warning(f"key {key} invalid, ignoring")
        self._update(to_update)

    def _update_all(self) -> None:
        self._update(self._map.values())

    def _update(self, states: Iterable[_LEDState]) -> None:
        if self._active:
            self._lp.sysex(
                sum(
                    (state.encode() for state in states),
                    SET_LED_PREAMBLE,
                )
            )


class _ScenePopper:
    def __init__(self, lp: "Launchpad"):
        self._lp = lp

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._lp.pop_scene()


class Launchpad:
    def __init__(self, loop, input_name: str = "", output_name: str = ""):
        self.on_raw_event = Signal()  # msg

        cb, self._stream = _make_stream(loop)

        self._event_callbacks = []
        self._key_callbacks = {}
        self._in = mido.open_input(input_name, callback=cb)
        self._out = mido.open_output(output_name)

        # set in programmer mode and clear all LEDs
        self._out.send(mido.Message("sysex", data=[0, 32, 41, 2, 13, 14, 1]))
        loop.create_task(self._process_messages())

        self._scene_stack = [Scene(self)]
        self._scene_stack[-1].activate()

    @property
    def scene(self) -> Scene:
        return self._scene_stack[-1]

    def push_scene(self, scene: Optional[Scene] = None) -> _ScenePopper:
        if scene is None:
            scene = Scene(self)

        self.scene.deactivate()
        self._scene_stack.append(scene)
        scene.activate()

        return _ScenePopper(self)

    def pop_scene(self) -> None:
        if len(self._scene_stack) < 2:
            logging.warning("pop_scene() called once more than push_scene()!!!")
            return

        self._scene_stack.pop().deactivate()
        self.scene.activate()

    def sysex(self, data: List[int]) -> None:
        self._out.send(mido.Message("sysex", data=data))

    def on_key_press(self, key: int):
        return self.scene.on_key_press(key)

    def set_key_color(
        self,
        key: int,
        a: int,
        b: Optional[int] = None,
        c: Optional[int] = None,
        *,
        mode: Optional[str] = None,
    ) -> None:
        self.scene.set_key_color(key, a, b, c, mode=mode)

    def set_keys_color(self, colors: List[Tuple[int, int, int, int]]) -> None:
        """Batch set RGB values for multiples keys at one."""
        self.scene.set_keys_color(colors)

    def clear_all(self):
        """Switch all LEDs off."""
        self.scene.clear_all()

    async def _process_messages(self):
        async for message in self._stream:
            self.on_raw_event(message)

            key = None
            if message.type == "control_change" and message.value == 127:
                key = message.control
            elif message.type == "note_on" and message.velocity == 127:
                key = message.note

            if key in ALL_KEYS:
                self.scene.trigger_on_key_press(key)


class Fader:
    def __init__(
        self,
        parent: Union[Launchpad, Scene],
        plus_key: int,
        minus_key: int,
        fader_keys: List[int],
        min_value: int = 0,
        max_value: int = 100,
        step: int = 1,
        value: Optional[int] = None,
        button_color: Tuple[int, int, int] = (0, 127, 0),
        fader_color: Tuple[int, int, int] = (0, 0, 127),
    ):
        self._on_value_changed = Signal()

        self._value = 0
        self._scene = parent if isinstance(parent, Scene) else parent.scene
        self._min_value = min_value
        self._max_value = max_value
        self._step = step
        self._fader_keys = fader_keys
        self._fader_color = fader_color

        self._scene.set_key_color(plus_key, *button_color)
        self._scene.set_key_color(minus_key, *button_color)
        self._scene.on_key_press(plus_key).connect(lambda k: self.on_plus())
        self._scene.on_key_press(minus_key).connect(lambda k: self.on_minus())
        for key in fader_keys:
            self._scene.on_key_press(key).connect(lambda k: self.on_fader_key(k))

        if value is not None:
            self.value = value
        else:
            self.value = round(min_value + (max_value - min_value) / 2)

    @property
    def on_value_changed(self) -> Signal:
        return self._on_value_changed

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, value: int):
        if value < self._min_value:
            value = self._min_value
        elif value > self._max_value:
            value = self._max_value

        old_value = self._value
        self._value = value

        # set fader led color
        key_count = (
            (value - self._min_value)
            / (self._max_value - self._min_value)
            * len(self._fader_keys)
        )
        solid_key_counts = math.floor(key_count)
        r, g, b = self._fader_color
        colors: List[Tuple[int, int, int, int]] = [
            (self._fader_keys[i], r, g, b) for i in range(solid_key_counts)
        ]
        fraction = key_count - solid_key_counts
        if solid_key_counts < len(self._fader_keys):
            colors.append(
                (
                    self._fader_keys[solid_key_counts],
                    int(fraction * r),
                    int(fraction * g),
                    int(fraction * b),
                )
            )

            for i in range(solid_key_counts + 1, len(self._fader_keys)):
                colors.append((self._fader_keys[i], 0, 0, 0))
        self._scene.set_keys_color(colors)
        if old_value != self._value:
            self._on_value_changed(self._value)

    def on_plus(self) -> None:
        self.value = self.value + self._step

    def on_minus(self) -> None:
        self.value = self.value - self._step

    def on_fader_key(self, key: int) -> None:
        idx = self._fader_keys.index(key)
        self.value = int(
            self._min_value
            + (self._max_value - self._min_value) * (idx + 1) / len(self._fader_keys)
        )


ValueType = TypeVar("ValueType")


class Selector:
    def __init__(
        self,
        parent: Union[Launchpad, Scene],
        values: List[ValueType],
        forward_key: int,
        back_key: int,
        forward_color: int,
        back_color: int,
    ):
        self._scene = parent if isinstance(parent, Scene) else parent.scene
        self._values = values
        self._current = 0

        self.on_value_change = Signal()

        self._scene.set_key_color(forward_key, forward_color)
        self._scene.set_key_color(back_key, back_color)
        self._scene.on_key_press(forward_key).connect(lambda k: self.rotate_value())
        self._scene.on_key_press(back_key).connect(lambda k: self.rotate_value(True))

    @property
    def value(self) -> Optional[ValueType]:
        if self._values:
            return self._values[self._current]
        else:
            return None

    @value.setter
    def value(self, value: ValueType) -> None:
        try:
            self._current = self._values.index(value)
            self.on_value_change(self._values[self._current])
        except IndexError:
            logging.warning(f"value '{value}' no found, ignoring")

    def rotate_value(self, backward: bool = False) -> None:
        if not self._values:
            return

        self._current += -1 if backward else 1
        self._current %= len(self._values)
        self.on_value_change(self._values[self._current])


class Checkbox:
    def __init__(
        self, parent: Union[Launchpad, Scene], key: int, color_on: int, color_off: int
    ):
        self.on_value_change = Signal()

        self._scene = parent if isinstance(parent, Scene) else parent.scene
        self._key = key
        self._color_on = color_on
        self._color_off = color_off

        self._scene.on_key_press(key).connect(lambda k: self.toggle())

        self.value = False

    @property
    def value(self) -> bool:
        return self._value

    @value.setter
    def value(self, val: bool) -> None:
        self._value = val
        self._scene.set_key_color(
            self._key, self._color_on if self._value else self._color_off
        )
        self.on_value_change(self._value)

    def toggle(self):
        self.value = not self.value
