from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nodan.core.node_system import Operation, PortSpec

SUBGRAPH_TYPE_PREFIX = "subgraph."


@dataclass
class SubgraphDefinition:
    id: str
    title: str
    input_spec: list[PortSpec]
    output_spec: list[PortSpec]
    graph_data: dict[str, Any]


def subgraph_type_id(subgraph_id: str) -> str:
    return f"{SUBGRAPH_TYPE_PREFIX}{subgraph_id}"


class SubgraphOperation(Operation):
    category = "Subgraph"
    subgraph: SubgraphDefinition | None = None

    def evaluate(self, inputs: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Subgraph execution is not implemented yet.")


def build_subgraph_operation(
    subgraph: SubgraphDefinition,
) -> type[SubgraphOperation]:
    attrs = {
        "type_id": subgraph_type_id(subgraph.id),
        "title": subgraph.title,
        "input_spec": list(subgraph.input_spec),
        "output_spec": list(subgraph.output_spec),
        "subgraph": subgraph,
    }
    class_name = f"Subgraph_{subgraph.id.replace('.', '_').replace('-', '_')}"
    return type(class_name, (SubgraphOperation,), attrs)


def register_subgraph_operation(
    subgraph: SubgraphDefinition,
) -> type[SubgraphOperation]:
    type_id = subgraph_type_id(subgraph.id)
    existing = Operation.registry.get(type_id)
    if existing is not None:
        return existing

    return build_subgraph_operation(subgraph)


def unregister_subgraph_operation(subgraph_id: str) -> None:
    Operation.registry.pop(subgraph_type_id(subgraph_id), None)
