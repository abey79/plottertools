ALLOWABLE_OPTION = [
    "speed_pendown",
    "speed_penup",
    "accel",
    "pen_pos_down",
    "pen_pos_up",
    "pen_rate_lower",
    "pen_rate_raise",
    "pen_delay_down",
    "pen_delay_up",
    "const_speed",
    "model",
    "port",
    "port_config",
    # plot context
    "mode",
    "manual_cmd",
    "walk_dist",
    "layer",
    "copies",
    "page_delay",
    "auto_rotate",
    "preview",
    "rendering",
    "reordering",
    "report_time",
    # interactive context
    "units",
]


_stub_print = print


def set_print_callback(cb):
    global _stub_print
    _stub_print = cb


# noinspection PyMethodMayBeStatic
class Axy:
    def __init__(self):
        _stub_print("STUB: __init__()")

    def __del__(self):
        _stub_print("STUB: __del__()")

    def set_option(self, option, value):
        if option not in ALLOWABLE_OPTION:
            raise ValueError(f"option {option} invalid")
        _stub_print(f"STUB: set_option({option}, {value})")

    def walk_x(self, x: float):
        _stub_print(f"STUB: walk_x({x})")

    def walk_y(self, y: float):
        _stub_print(f"STUB: walk_y({y})")

    def plot_svg(self, svg: str):
        _stub_print(f"STUB: plot_svg(str_len={len(svg)})")

    def shutdown(self):
        _stub_print(f"STUB: shutdown()")

    def pen_up(self):
        _stub_print(f"STUB: pen_up()")

    def pen_down(self):
        _stub_print(f"STUB: pen_down()")


axy = Axy()
