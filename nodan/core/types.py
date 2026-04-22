import numbers
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PortType:
    name: str
    check: Callable[[Any], bool]
    coerce: Callable[[Any], Any] | None = None

    def accepts(self, value: Any) -> bool:
        return self.check(value)

    def normalize(self, value: Any) -> Any:
        if not self.accepts(value):
            raise TypeError(f"{self.name} does not accept {type(value).__name__}")

        if self.coerce is None:
            return value

        return self.coerce(value)


# === Number type ===
def is_number(value: Any) -> bool:
    return isinstance(value, (numbers.Number, np.number))


Number = PortType("number", is_number)


# === Array type ===
def is_array(value: Any) -> bool:
    return isinstance(value, (pd.DataFrame, pd.Series, np.ndarray, list, tuple))


def coerce_array(value: Any) -> pd.DataFrame:
    if isinstance(value, pd.DataFrame):
        return value

    if isinstance(value, pd.Series):
        return value.to_frame()

    if isinstance(value, np.ndarray):
        return pd.DataFrame(value)

    if isinstance(value, (list, tuple)):
        return pd.DataFrame(value)

    raise TypeError(f"Cannot convert {type(value).__name__} to array")


Array = PortType(name="array", check=is_array, coerce=coerce_array)


# === Text type ===
def is_text(value: Any) -> bool:
    return isinstance(value, str)


Text = PortType(name="text", check=is_text, coerce=None)


# === Bool type ===
def is_bool(value: Any) -> bool:
    return isinstance(value, bool)


Bool = PortType(name="bool", check=is_bool, coerce=None)
