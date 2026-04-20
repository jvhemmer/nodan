from nodan.core.node_system import CoreNode, CoreConnection
from typing import Any

class Graph:
    def __init__(self):
        self.nodes: dict[str, CoreNode] = {}
        self.connections: list[CoreConnection] = []

    def add_node(self, node: CoreNode):
        self.nodes[node.id] = node

    def connect(self, source_node_id: str, source_port: str, target_node_id: str, target_port: str):
        self.connections.append(CoreConnection(source_node_id, source_port, target_node_id, target_port))

class Executor:
    def __init__(self, graph: Graph):
        self.graph = graph
        self.cache: dict[str, dict[str, Any]] = {}

    def evaluate_node(self, node_id: str) -> dict[str, Any]:
        if node_id in self.cache:
            return self.cache[node_id]

        node = self.graph.nodes[node_id]
        resolved_inputs: dict[str, Any] = {}

        for input_port in node.inputs:
            input_name = input_port.spec.name
            matching_connection = None

            for connection in self.graph.connections:
                is_correct_target_node = connection.target_node_id == node_id
                is_correct_target_port = connection.target_port == input_name

                if is_correct_target_node and is_correct_target_port:
                    matching_connection = connection
                    break

            if matching_connection is not None:
                upstream_outputs = self.evaluate_node(matching_connection.source_node_id)
                value = upstream_outputs[matching_connection.source_port]
                input_port.value = value
                resolved_inputs[input_name] = value
                continue

            resolved_inputs[input_name] = input_port.value

        outputs = node.definition.evaluate(resolved_inputs, node.params)

        for output_port in node.outputs:
            output_port.value = outputs.get(output_port.spec.name)

        self.cache[node_id] = outputs
        return outputs
