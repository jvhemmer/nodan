from dataclasses import dataclass
from typing import Any, ClassVar

PortTypeRef = str | list[str]


def normalize_data_types(data_type: PortTypeRef) -> tuple[str, ...]:
    if isinstance(data_type, str):
        return (data_type,)

    return tuple(data_type)


def format_data_type(data_type: PortTypeRef) -> str:
    return " | ".join(normalize_data_types(data_type))


@dataclass
class PortSpec:
    name: str
    data_type: PortTypeRef
    default: Any = None
    editable: bool = False
    hideable: bool = False

    def data_types(self) -> tuple[str, ...]:
        return normalize_data_types(self.data_type)


@dataclass
class RepeatedInputSpec:
    base_name: str
    data_type: PortTypeRef
    min_count: int = 2
    default_count: int = 2
    editable: bool = False

    def data_types(self) -> tuple[str, ...]:
        return normalize_data_types(self.data_type)


@dataclass(frozen=True)
class Operation:
    registry: ClassVar[dict[str, type["Operation"]]] = {}

    type_id: ClassVar[str] = ""
    title: ClassVar[str] = ""
    category: ClassVar[str] = "General"

    input_spec: ClassVar[list[PortSpec]] = []
    output_spec: ClassVar[list[PortSpec]] = []
    repeated_inputs: ClassVar[RepeatedInputSpec | None] = None

    def __init__(self):
        self.validate_ports()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if not cls.type_id:
            return

        if cls.type_id in Operation.registry:
            raise ValueError(f"Duplication operation type_id: {cls.type_id}")

        Operation.registry[cls.type_id] = cls

    def get_input_ports(self, instance) -> list[PortSpec]:
        ports = list(self.input_spec)

        if self.repeated_inputs is not None:
            count = instance.state.get(
                "input_count", self.repeated_inputs.default_count
            )
            for i in range(count):
                ports.append(
                    PortSpec(
                        f"{self.repeated_inputs.base_name}{i + 1}",
                        self.repeated_inputs.data_type,
                        editable=self.repeated_inputs.editable,
                    )
                )

        return ports

    def evaluate(self, inputs: dict[str, Any]) -> dict[str, Any] | None:
        raise NotImplementedError

    def validate_ports(self):
        seen_inputs = set()
        for port in self.input_spec:
            if port.name in seen_inputs:
                raise ValueError(f"Duplicate input port {port.name}")
            seen_inputs.add(port.name)

        seen_outputs = set()
        for port in self.output_spec:
            if port.name in seen_outputs:
                raise ValueError(f"Duplicate output port {port.name}")
            seen_outputs.add(port.name)


@dataclass
class CorePort:
    node_id: str
    kind: str
    spec: PortSpec
    value: Any = None


@dataclass
class CoreNode:
    id: str
    definition: Operation
    params: dict[str, Any]
    state: dict[str, Any]
    inputs: list[CorePort]
    outputs: list[CorePort]

    def build_node_ports(self) -> tuple[list[CorePort], list[CorePort]]:
        inputs = [
            CorePort(self.id, kind="input", spec=spec, value=spec.default)
            for spec in self.definition.get_input_ports(self)
        ]
        outputs = [
            CorePort(self.id, kind="output", spec=spec, value=spec.default)
            for spec in self.definition.output_spec
        ]
        self.inputs = inputs
        self.outputs = outputs
        return inputs, outputs

    def get_input_port(self, name: str) -> CorePort | None:
        for port in self.inputs:
            if port.spec.name == name:
                return port
        return None

    def get_output_port(self, name: str) -> CorePort | None:
        for port in self.outputs:
            if port.spec.name == name:
                return port
        return None


@dataclass
class CoreConnection:
    source_node_id: str
    source_port: str
    target_node_id: str
    target_port: str
