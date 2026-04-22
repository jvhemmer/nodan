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
    parser: Callable[[str], Any] | None = None

    def accepts(self, value: Any) -> bool:
        return self.check(value)

    def normalize(self, value: Any) -> Any:
        if not self.accepts(value):
            raise TypeError(f"{self.name} does not accept {type(value).__name__}")

        if self.coerce is None:
            return value

        return self.coerce(value)

    def parse(self, raw_value: str) -> Any:
        if self.parser is None:
            return raw_value

        return self.parser(raw_value)


# === Number type ===
def is_number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (numbers.Number, np.number))


def parse_number(raw_value: str) -> Any:
    value = raw_value.strip()
    if value == "":
        return None

    try:
        return float(value) if "." in value else int(value)
    except ValueError:
        return value


Number = PortType(name="number", check=is_number, parser=parse_number)


# === Table type ===
def is_table(value: Any) -> bool:
    return isinstance(value, (pd.DataFrame, pd.Series, np.ndarray, list, tuple))


def coerce_table(value: Any) -> pd.DataFrame:
    if isinstance(value, pd.DataFrame):
        return value

    if isinstance(value, pd.Series):
        return value.to_frame()

    if isinstance(value, np.ndarray):
        return pd.DataFrame(value)

    if isinstance(value, (list, tuple)):
        return pd.DataFrame(value)

    raise TypeError(f"Cannot convert {type(value).__name__} to table")


Table = PortType(name="table", check=is_table, coerce=coerce_table)
Array = PortType(name="array", check=is_table, coerce=coerce_table)


# === DataFrame type ===
def is_dataframe(value: Any) -> bool:
    return isinstance(value, pd.DataFrame)


DataFrame = PortType(name="dataframe", check=is_dataframe)


# === Text type ===
def is_text(value: Any) -> bool:
    return isinstance(value, str)


Text = PortType(name="text", check=is_text, coerce=None)


# === Bool type ===
def is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def parse_bool(raw_value: str) -> bool:
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


Bool = PortType(name="bool", check=is_bool, coerce=None, parser=parse_bool)


# === Data/Object types ===
def is_data(value: Any) -> bool:
    return True


Data = PortType(name="data", check=is_data)
Object = PortType(name="object", check=is_data)


PORT_TYPES: dict[str, PortType] = {
    "any": Data,
    "array": Array,
    "bool": Bool,
    "data": Data,
    "dataframe": DataFrame,
    "number": Number,
    "object": Object,
    "scalar": Number,
    "string": Text,
    "table": Table,
    "text": Text,
}


def get_port_type(name: str) -> PortType:
    return PORT_TYPES.get(name, Object)
