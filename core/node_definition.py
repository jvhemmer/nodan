from dataclasses import dataclass
from typing import Any

@dataclass
class PortSpec:
    name: str
    data_type: str

@dataclass
class ParamSpec:
    name: str
    param_type: str
    default: Any = None

@dataclass
class RepeatedInputSpec:
    base_name: str
    data_type: str
    min_count: int = 2
    default_count: int = 2

class Operation:
    type_id = ""
    title = ""
    category = "General"

    inputs: tuple[PortSpec, ...] = ()
    outputs: tuple[PortSpec, ...] = ()
    repeated_inputs: RepeatedInputSpec | None = None

    def get_input_ports(self, instance) -> list[PortSpec]:
        ports = list(self.inputs)

        if self.repeated_inputs is not None:
            count = instance.state.get("input_count", self.repeated_inputs.default_count)
            for i in range(count):
                ports.append(
                    PortSpec(f"{self.repeated_inputs.base_name}{i + 1}", self.repeated_inputs.data_type)
                )

        return ports

    def evaluate(self, inputs: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def __init__(self):
        self.validate_ports()

    def validate_ports(self):
        seen_inputs = set()
        for port in self.inputs:
            if port.name in seen_inputs:
                raise ValueError(f"Duplicate input port {port.name}")
            seen_inputs.add(port.name)

        seen_outputs = set()
        for port in self.outputs:
            if port.name in seen_outputs:
                raise ValueError(f"Duplicate output port {port.name}")
            seen_outputs.add(port.name)


class ConstantValue(Operation):
    type_id = "value.constant"
    title = "Constant"
    category = "Values"

    inputs = []
    outputs = [PortSpec("value", "any")]
    params = [ParamSpec("value", "any", 0)]

    def evaluate(self, inputs: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
        return {"value": params["value"]}

class DebugLog(Operation):
    type_id = "debug.log"
    title = "Log"
    category = "Debug"

    inputs = [PortSpec("value", "any")]
    outputs = []
    params = []

    def evaluate(self, inputs: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
        value = inputs["value"]
        print(value)

class MultiplyValue(Operation):
    type_id = "multiply.value"
    title = "Multiply"
    category = "Basic operation"

    repeated_inputs = RepeatedInputSpec(
        base_name="value",
        data_type="number",
        min_count=2,
        default_count=2,
    )

    outputs = (PortSpec("result", "number"),)

    def evaluate(self, inputs: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
        result = 1
        for value in inputs.values():
            result *= value
        return {"result": result}

@dataclass
class CoreConnection:
    source_node_id: str
    source_port: str
    target_node_id: str
    target_port: str

@dataclass
class CoreNode:
    id: str
    definition: Operation
    params: dict[str, Any]
    state: dict[str, Any]