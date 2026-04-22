from typing import Any

from nodan.core.types import get_port_type


class PortValueParser:
    def parse(self, data_type: str, raw_value: str) -> Any:
        return get_port_type(data_type).parse(raw_value)
