import configparser
import os
from typing import Any, Dict, TypeVar

config_path = os.path.expanduser("~/.aximix.ini")
config = configparser.ConfigParser()
config.read(config_path)
if "__persistent__" not in config:
    config["__persistent__"] = {}


def save_config():
    with open(config_path, "w") as f:
        config.write(f)


VarType = TypeVar("VarType")


class PersistentVar:
    def __init__(self, name: str, default: VarType):
        self._name = name
        self._default: VarType = default
        self._type = type(default)

    @property
    def value(self) -> VarType:
        cfg = config["__persistent__"]
        if self._type is bool:
            # special case needed because bool("False") == True
            # noinspection PyArgumentList
            return cfg.getboolean(self._name, self._default)
        else:
            return self._type(cfg.get(self._name, self._default))

    def set_value(self, value: VarType):
        config["__persistent__"][self._name] = str(value)
        save_config()


def get_axidraw_config() -> Dict[str, Any]:
    params = {
        "speed_penup": int,
        "pen_rate_lower": int,
        "pen_rate_raise": int,
        "pen_delay_down": int,
        "pen_delay_up": int,
        "const_speed": bool,
        "model": int,
        "port": str,
        "port_config": int,
    }

    res = {}
    for key, t in params.items():
        if key in config["axidraw"]:
            if t is bool:
                res[key] = config["axidraw"].getboolean(key)
            else:
                res[key] = t(config["axidraw"][key])

    return res


def get_setting(key: str) -> str:
    return config["aximix"][key]
