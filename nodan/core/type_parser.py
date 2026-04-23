from typing import Any

from nodan.core.node_system import PortTypeRef, normalize_data_types
from nodan.core.types import get_port_type


class PortValueParser:
    def parse(self, data_type: PortTypeRef, raw_value: str) -> Any:
        parsed_values: list[Any] = []

        for type_name in normalize_data_types(data_type):
            port_type = get_port_type(type_name)
            parsed = port_type.parse(raw_value)
            if port_type.accepts(parsed):
                return parsed
            parsed_values.append(parsed)

        if parsed_values:
            return parsed_values[0]

        return raw_value
