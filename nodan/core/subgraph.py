from dataclasses import dataclass
from typing import ClassVar, Any

from nodan.core.document import GraphDocument
from nodan.core.graph import Executor
from nodan.core.node_system import PortSpec, PortTypeRef, Operation


def build_subgraph_definition(
    doc: GraphDocument,
    *,
    subgraph_id: str,
    name: str,
) -> SubgraphDefinition:
    graph = doc.to_graph()

    input_bindings: list[SubgraphInputBinding] = []
    output_bindings: list[SubgraphOutputBinding] = []

    for node_doc in doc.nodes:
        node = graph.nodes[node_doc.id]
        node_name = node_doc.name or node.definition.name

        for port in node.inputs:
            if graph.input_port_is_connected(node.id, port.spec.name):
                continue

            input_bindings.append(
                SubgraphInputBinding(
                    exposed_name=f"{node_name}.{port.spec.name}",
                    node_id=node.id,
                    port_name=port.spec.name,
                    data_type=port.spec.data_type,
                )
            )

        for port in node.outputs:
            output_bindings.append(
                SubgraphOutputBinding(
                    exposed_name=f"{node_name}.{port.spec.name}",
                    node_id=node.id,
                    port_name=port.spec.name,
                    data_type=port.spec.data_type,
                )
            )

    return SubgraphDefinition(
        id=subgraph_id,
        name=name,
        document=doc,
        input_bindings=input_bindings,
        output_bindings=output_bindings,
    )


@dataclass(frozen=True)
class SubgraphInputBinding:
    exposed_name: str
    node_id: str
    port_name: str
    data_type: PortTypeRef


@dataclass(frozen=True)
class SubgraphOutputBinding:
    exposed_name: str
    node_id: str
    port_name: str
    data_type: PortTypeRef


@dataclass
class SubgraphDefinition:
    id: str
    name: str
    document: GraphDocument
    input_bindings: list[SubgraphInputBinding]
    output_bindings: list[SubgraphOutputBinding]

    @property
    def input_spec(self) -> list[PortSpec]:
        return [
            PortSpec(binding.exposed_name, binding.data_type)
            for binding in self.input_bindings
        ]

    @property
    def output_spec(self) -> list[PortSpec]:
        return [
            PortSpec(binding.exposed_name, binding.data_type)
            for binding in self.output_bindings
        ]

class SubgraphOperation(Operation):
    category = "Subgraph"
    subgraph: ClassVar[SubgraphDefinition | None] = None

    def evaluate(self, inputs: dict[str, Any]) -> dict[str, Any]:
        if self.subgraph is None:
            raise ValueError("Subgraph definition missing.")

        graph = self.subgraph.document.to_graph()
        executor = Executor(graph)

        for binding in self.subgraph.input_bindings:
            if binding.exposed_name not in inputs:
                continue

            node = graph.nodes[binding.node_id]
            port = node.get_input_port(binding.port_name)
            if port is not None:
                port.value = inputs[binding.exposed_name]

        results: dict[str, Any] = {}

        for binding in self.subgraph.output_bindings:
            outputs = executor.evaluate_node(binding.node_id)
            if outputs is None:
                continue

            results[binding.exposed_name] = outputs.get(binding.port_name)

        return results